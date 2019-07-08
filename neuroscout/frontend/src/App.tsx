/*
Top-level App component containing AppState. The App component is currently responsible for:
- Authentication (signup, login and logout)
- Routing
- Managing user's saved analyses (list display, clone and delete)
*/
import * as React from 'react';
import { BrowserRouter as Router, Route, Link, Redirect, Switch } from 'react-router-dom';
import Reflux from 'reflux';
import { Avatar, Divider, Tabs, Row, Col, Layout, Button, Menu, Modal, Icon, Input, Form, message } from 'antd';
import { GoogleLogin } from 'react-google-login';

import NotFound from './404';
import './App.css';
import { api } from './api';
import { AuthStore } from './auth.store';
import { authActions } from './auth.actions';
import AnalysisBuilder from './Builder';
import { config } from './config';
import { ApiUser, ApiAnalysis, AppAnalysis, AuthStoreState, Dataset } from './coretypes';
import FAQ from './FAQ';
import { MainCol, Space } from './HelperComponents';
import Home from './Home';
import Private from './Private';
import Public from './Public';
import { displayError, jwtFetch, timeout } from './utils';
import Tour from './Tour';

const FormItem = Form.Item;
const DOMAINROOT = config.server_url;
const GOOGLECLIENTID = config.google_client_id;
const { localStorage } = window;

const { Header, Content, Footer, Sider } = Layout;

type JWTChangeProps = {
  loadAnalyses:  () => any;
  checkAnalysesStatus: (key: number) => any;
};

// This global var lets the dumb polling loops know when to exit.
let checkCount = 0;

class JWTChange extends React.Component<JWTChangeProps, {}> {
  constructor(props) {
    super(props);
    props.loadAnalyses();
    checkCount += 1;
    props.checkAnalysesStatus(checkCount);
  }

  render() { return null; }
}

class GoogleLoginBtn extends React.Component<{}, {}> {
  render() {
    return (
      <GoogleLogin
        clientId={GOOGLECLIENTID}
        render={renderProps => (
          <Button
            onClick={renderProps && renderProps.onClick}
            style={{ width: '100%' }}
            htmlType="submit"
            type="primary"
            ghost={true}
          >
            <Icon type="google" />
          </Button>
        )}
        buttonText="Log in"
        onSuccess={(e) => {
          if (e.hasOwnProperty('accessToken')) {
            authActions.update({
              email: 'GOOGLE',
              password: (e as any).tokenId,
              gAuth: e,
              openSignup: false,
              openLogin: false
            });
            authActions.login();
          }
          return '';
        }}
        onFailure={(e) => {
          return '';
        }}
      />
    );
  }
}

interface AppState {
  loadAnalyses: boolean;
  analyses: AppAnalysis[]; // List of analyses belonging to the user
  publicAnalyses: AppAnalysis[]; // List of public analyses
  auth: AuthStoreState;
  datasets: Dataset[];
}

// Convert analyses returned by API to the shape expected by the frontend
const ApiToAppAnalysis = (data: ApiAnalysis): AppAnalysis => ({
  id: data.hash_id!,
  name: data.name,
  description: data.description,
  status: data.status,
  datasetName: !!data.dataset_id ? '' + data.dataset_id : '',
  modifiedAt: data.modified_at
});

// Top-level App component
class App extends Reflux.Component<any, {}, AppState> {
  constructor(props) {
    super(props);
    this.state = {
      loadAnalyses: true,
      analyses: [],
      publicAnalyses: [],
      auth: authActions.getInitialState(),
      datasets: [],
    };
    this.store = AuthStore;
    this.loadPublicAnalyses();
    api.getDatasets(false).then((datasets) => {
      if (datasets.length !== 0) {
        this.setState({ datasets });
      }
    });
  }

  // Load user's saved analyses from the server
  loadAnalyses = () => {
    if (this.state.auth.loggedIn) {
      return jwtFetch(`${DOMAINROOT}/api/user`)
        .then((data: ApiUser) => {
          authActions.update({
            name: (data.name || []),
            email: (data.email || []),
            avatar: (data.picture || [])
          });
          this.setState({
            analyses: (data.analyses || [])
              .filter(x => !!x.status) // Ignore analyses with missing status
              .map((x) => ApiToAppAnalysis(x))
          });
        })
        .catch(displayError);
    } else {
      this.setState({analyses: []});
    }
    return;
  };

  // Load public analyses from the server
  loadPublicAnalyses = () =>
    fetch(`${DOMAINROOT}/api/analyses`)
      .then((response) => {
        return response.json();
      })
      .then((data: ApiAnalysis[]) => {
        this.setState({
          publicAnalyses: data
            .filter(x => !!x.status) // Ignore analyses with missing status
            .map(x => ApiToAppAnalysis(x))
        });
      })
      .catch(displayError);

  /* short polling function checking api for inprocess analyses to see if
   * there have been any changes
   */
  checkAnalysesStatus = async (key: number) => {
    while (true) {
      if (key < checkCount) { return; }
      if (!(this.state.auth.loggedIn)) { return; }
      let changeFlag = false;
      let updatedAnalyses = this.state.analyses.map(async (analysis) => {
        if (['DRAFT', 'PASSED'].indexOf(analysis.status) > -1) {
          return analysis;
        }
        let id = analysis.id;
        return jwtFetch(`${DOMAINROOT}/api/analyses/${id}`, { method: 'get' })
          .then((data: ApiAnalysis) => {
            if ((data.status !== analysis.status)
                && (['SUBMITTING', 'PENDING'].indexOf(data.status) === -1)) {
              changeFlag = true;
              message.info(`analysis ${id} updated from ${analysis.status} to ${data.status}`);
              analysis.status = data.status;
            }
            return analysis;
        })
        .catch(() => { return analysis; });
      });
      Promise.all(updatedAnalyses).then((values) => {
        if (changeFlag) {
          this.setState({ analyses: values});
        }
      });
      await timeout(10000000);
    }
  };

  setStateFromInput = (name: keyof AppState) => (event: React.FormEvent<HTMLInputElement>) => {
    const newState = {};
    newState[name] = event.currentTarget.value;
    this.setState(newState);
  };

  // Actually delete existing analysis given its hash ID, called from onDelete()
  deleteAnalysis = (id): void => {
      jwtFetch(`${DOMAINROOT}/api/analyses/${id}`, { method: 'delete' })
      .then((data: ApiAnalysis) => {
        this.setState({ analyses: this.state.analyses.filter(a => a.id !== id) });
      })
      .catch(displayError);
  };

  // Delete analysis if the necessary conditions are met
  onDelete = (analysis: AppAnalysis) => {
    const { deleteAnalysis } = this;
    if (analysis.status && ['DRAFT', 'FAILED'].includes(analysis.status) === false) {
      message.warning('This analysis has already been submitted and cannot be deleted.');
      return;
    }
    Modal.confirm({
      title: 'Are you sure you want to delete this analysis?',
      content: '',
      okText: 'Yes',
      cancelText: 'No',
      onOk() {
        deleteAnalysis(analysis.id);
      }
    });
  };

  // Clone existing analysis
  cloneAnalysis = (id): void => {
    jwtFetch(`${DOMAINROOT}/api/analyses/${id}/clone`, { method: 'post' })
      .then((data: ApiAnalysis) => {
        const analysis = ApiToAppAnalysis(data);
        this.setState({ analyses: this.state.analyses.concat([analysis]) });
      })
      .catch(displayError);
  };

  render() {
    const {
      loggedIn,
      email,
      name,
      token,
      openLogin,
      openSignup,
      openReset,
      openEnterResetToken,
      resetError,
      loginError,
      signupError,
      password,
      loggingOut,
      avatar,
      gAuth
    } = this.state.auth;

    let {
      analyses,
      publicAnalyses,
    } = this.state;
    if (loggingOut)
      return (
        <Router>
          <Redirect to="/" />
        </Router>
      );

    const resetPasswordModal = () => (
      <Modal
        title="Reset password"
        visible={openReset}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          authActions.update({openReset: false});
        }}
      >
        <p>
         Please enter an email address to send reset instructions
        </p>
        <Form
          onSubmit={e => {
            e.preventDefault();
            authActions.resetPassword();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="mail" style={{ fontSize: 13 }}/>}
              placeholder="Email"
              type="email"
              size="large"
              value={email}
              onChange={authActions.updateFromInput('email')}
            />
          </FormItem>
          <FormItem>
            <Button style={{ width: '100%' }} htmlType="submit" type="primary">
              Reset password
            </Button>
          </FormItem>
        </Form>
      </Modal>
  );

    const enterResetTokenModal = () => (
      <Modal
        title="Change password"
        visible={openEnterResetToken}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          authActions.update({ openEnterResetToken: false });
        }}
      >
        <p>
         We have sent a reset token to {email} <br/>
         Please enter the token below, along with a new password for the account.
       </p>
        <Form
          onSubmit={e => {
            e.preventDefault();
            authActions.submitToken();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="tags" style={{ fontSize: 13 }}/>}
              placeholder="Token"
              type="token"
              size="large"
              onChange={authActions.updateFromInput('token')}

            />
          </FormItem>
          <FormItem>
            <Input
              prefix={<Icon type="lock" style={{ fontSize: 13 }}/>}
              placeholder="Password"
              type="password"
              size="large"
              onChange={authActions.updateFromInput('password')}
            />
          </FormItem>
          <FormItem>
            <Button style={{ width: '100%' }} htmlType="submit" type="primary">
              Submit
            </Button>
          </FormItem>
        </Form>
        <p>
          {resetError}
        </p>
        <br />
      </Modal>
  );

    const loginModal = () => (
      <Modal
        title="Log into Neuroscout"
        visible={this.state.auth.openLogin}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          authActions.logout();
          authActions.update({ openLogin: false });
        }}
      >
        <p>
          {loginError ? loginError : ''}
        </p>
        <br />
        <Form
          onSubmit={e => {
            e.preventDefault();
            authActions.login();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="mail" style={{ fontSize: 13 }}/>}
              placeholder="Email"
              type="email"
              size="large"
              value={email}
              onChange={(e) => {
                authActions.updateFromInput('email', e);
              }}
            />
          </FormItem>
          <FormItem>
            <Input
              prefix={<Icon type="lock" style={{ fontSize: 13 }}/>}
              placeholder="Password"
              type="password"
              value={this.state.auth.password}
              onChange={(e) => authActions.updateFromInput('password', e)}
            />
          </FormItem>
          <FormItem>
           <a onClick={e => {authActions.update( { openLogin: false, openReset: true}); }}>Forgot password</a><br/>
            <Button style={{ width: '100%' }} htmlType="submit" type="primary">
              Log in
            </Button>
          </FormItem>
        </Form>
        <Divider> Or log in with Google </Divider>
        <GoogleLoginBtn />
      </Modal>
    );

    const signupModal = (
      <Modal
        title="Sign up for a Neuroscout account"
        visible={openSignup}
        footer={null}
        maskClosable={true}
        onCancel={e => authActions.update({ openSignup: false }, e)}
      >
        <p>
          {this.state.auth.signupError}
        </p>
        <br />
        <Form
          onSubmit={e => {
            e.preventDefault();
            authActions.signup();
          }}
        >
          <FormItem>
            <Input
              placeholder="Full name"
              size="large"
              value={name}
              onChange={(e) => authActions.updateFromInput('name', e)}
            />
          </FormItem>
          <FormItem>
            <Input
              placeholder="Email"
              type="email"
              size="large"
              value={email}
              onChange={(e) => authActions.updateFromInput('email', e)}
            />
          </FormItem>
          <FormItem>
            <Input
              placeholder="Password"
              type="password"
              value={password}
              onChange={(e) => authActions.updateFromInput('password', e)}
            />
          </FormItem>
          <FormItem>
            <Button style={{ width: '100%' }} type="primary" htmlType="submit">
              Sign up
            </Button>
          </FormItem>
        </Form>
        <Divider> Or sign up using a Google account </Divider>
        <GoogleLoginBtn />
      </Modal>
    );

    return (
      <Router>
        <div>
          <JWTChange
            loadAnalyses={this.loadAnalyses}
            checkAnalysesStatus={this.checkAnalysesStatus}
            key={this.state.auth.jwt}
          />
          {openLogin && loginModal()}
          {openReset && resetPasswordModal()}
          {openSignup && signupModal}
          {openEnterResetToken && authActions.enterResetTokenModal()}
          <Layout>
            <Tour
              isOpen={this.state.auth.openTour}
              closeTour={authActions.closeTour}
            />
            <Content style={{ background: '#fff' }}>
            <Row type="flex" justify="center" style={{padding: 0 }}>
              <MainCol>
                <Menu
                  mode="horizontal"
                  style={{ lineHeight: '64px'}}
                  selectedKeys={[]}
                >
                  <Menu.Item className="menuHome" key="home">
                     <Link to="/" style={{fontSize: 20}}>Neuroscout</Link>
                  </Menu.Item>
                  {this.state.auth.loggedIn ?
                    <Menu.SubMenu
                      style={{float: 'right'}}
                      title={
                        <Avatar
                          shape="circle"
                          icon="user"
                          src={avatar ? avatar : gAuth ? gAuth.profileObj.imageUrl : ''}
                          className="headerAvatar"
                        />
                      }
                    >

                       <Menu.ItemGroup title={`${gAuth ? gAuth.profileObj.email : email}`}>
                         <Menu.Divider/>
                         <Menu.Item
                          key="signout"
                          onClick={(e) => {return authActions.confirmLogout(); }}
                         >
                          Sign Out
                         </Menu.Item>
                       </Menu.ItemGroup>
                    </Menu.SubMenu>
                   :
                    <Menu.Item key="signup" style={{float: 'right'}}>
                    <Button size="large" type="primary" onClick={e => authActions.update({ openSignup: true })}>
                      Sign up</Button></Menu.Item>
                   }
                   {this.state.auth.loggedIn === false &&
                       <Menu.Item
                        onClick={e => authActions.update({ openLogin: true })}
                        key="signin"
                        style={{float: 'right'}}
                       >
                         Sign in
                       </Menu.Item>
                    }
                   <Menu.SubMenu
                    style={{float: 'right'}}
                    key="help"
                    title={<span><Icon type="question-circle"/>Help</span>}
                   >
                     <Menu.Item
                      key="faq"
                     >
                      <Link to="/faq">
                        FAQ
                      </Link>
                     </Menu.Item>
                   </Menu.SubMenu>

                   <Menu.SubMenu
                    style={{float: 'right'}}
                    key="browse"
                    className="browseMain"
                    title={<span><Icon type="search"/>Browse</span>}
                   >

                     {this.state.auth.loggedIn &&
                       <Menu.Item key="mine" >
                        <Link to="/myanalyses">
                          My analyses
                        </Link>
                       </Menu.Item>
                    }
                     <Menu.Item
                      className="browsePublic"
                      key="public"
                     >
                     <Link to="/public">
                      Public analyses
                      </Link>
                     </Menu.Item>
                   </Menu.SubMenu>

                   {this.state.auth.loggedIn &&
                     <Menu.Item className="newAnalysis" key="create" style={{float: 'right'}}>
                       <Link
                         to={{pathname: '/builder'}}
                       >
                         <Icon type="plus" /> New Analysis
                       </Link>
                     </Menu.Item>
                   }

                </Menu>
              </MainCol>
            </Row>
              <br />
              <Switch>
                <Route
                  exact={true}
                  path="/"
                  render={props =>
                    <Home />
                   }
                />
                <Route
                  exact={true}
                  path="/builder"
                  render={props => {
                    // This is a temporary solution to prevent non logged-in users from entering the builder.
                    // Longer term to automatically redirect the user to the target URL after login we
                    // need to implement something like the auth workflow example here:
                    // https://reacttraining.com/react-router/web/example/auth-workflow
                    if (loggedIn || this.state.auth.openLogin) {
                      return <AnalysisBuilder
                                updatedAnalysis={() => this.loadAnalyses()}
                                key={props.location.key}
                                doTour={this.state.auth.openTour}
                                datasets={this.state.datasets}
                      />;
                    }
                    message.warning('Please log in first and try again');
                    return <Redirect to="/" />;
                  }}
                />
                <Route
                  path="/builder/:id"
                  render={props =>
                    <AnalysisBuilder
                      id={props.match.params.id}
                      updatedAnalysis={() => this.loadAnalyses()}
                      userOwns={this.state.analyses.filter((x) => x.id === props.match.params.id).length > 0}
                      doTooltip={true}
                      datasets={this.state.datasets}
                    />}
                />
                <Route
                  exact={true}
                  path="/public/:id"
                  render={props =>
                    <AnalysisBuilder
                      id={props.match.params.id}
                      updatedAnalysis={() => this.loadAnalyses()}
                      userOwns={this.state.analyses.filter((x) => x.id === props.match.params.id).length > 0}
                      doTooltip={true}
                      datasets={this.state.datasets}
                    />
                  }
                />
              <Route
                exact={true}
                path="/public"
                render={props =>
                  <Public
                    analyses={publicAnalyses}
                    cloneAnalysis={this.cloneAnalysis}
                    datasets={this.state.datasets}
                  />}
              />
              <Route
                exact={true}
                path="/myanalyses"
                render={props =>
                  <Private
                    analyses={analyses}
                    cloneAnalysis={this.cloneAnalysis}
                    onDelete={this.onDelete}
                    datasets={this.state.datasets}
                  />}
              />
              <Route
                exact={true}
                path="/faq"
                render={() => <FAQ/>}
              />
              <Route render={() => <NotFound/>} />
              </Switch>
            </Content>
          </Layout>
        </div>
      </Router>
    );
  }

  componentDidUpdate(prevProps, prevState) {
    // Need to do this so logout redirect only happens once, otherwise it'd be an infinite loop
    if (this.state.auth.loggingOut) authActions.update({ loggingOut: false });
  }
}

export default App;
