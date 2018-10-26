/*
Top-level App component containing AppState. The App component is currently responsible for:
- Authentication (signup, login and logout)
- Routing
- Managing user's saved analyses (list display, clone and delete)
*/
import * as React from 'react';
import { BrowserRouter as Router, Route, Link, Redirect } from 'react-router-dom';
import Reflux from 'reflux';
import { Tabs, Row, Col, Layout, Button, Modal, Icon, Input, Form, message } from 'antd';

import './App.css';
import AnalysisBuilder from './Builder';
import { ApiUser, ApiAnalysis, AppAnalysis, AuthStoreState } from './coretypes';
import Browse from './Browse';
import { config } from './config';
import Home from './Home';
import { Space } from './HelperComponents';
import { displayError, jwtFetch, timeout } from './utils';
import { AuthStore } from './auth.store';
import { authActions } from './auth.actions';

const FormItem = Form.Item;
const DOMAINROOT = config.server_url;
const { localStorage } = window;

const { Footer, Content, Header } = Layout;

interface AppState {
  loadAnalyses: boolean;
  analyses: AppAnalysis[]; // List of analyses belonging to the user
  publicAnalyses: AppAnalysis[]; // List of public analyses
  auth: AuthStoreState;
}

// Convert analyses returned by API to the shape expected by the frontend
const ApiToAppAnalysis = (data: ApiAnalysis): AppAnalysis => ({
  id: data.hash_id!,
  name: data.name,
  description: data.description,
  status: data.status,
  modifiedAt: data.modified_at
});

// Top-level App component
// <authStore, {}, AppState>
class App extends Reflux.Component<any, {}, AppState> {
  constructor(props) {
    super(props);
    this.state = {
      loadAnalyses: true,
      analyses: [],
      publicAnalyses: [],
      auth: authActions.getInitialState()
    };
    this.store = AuthStore;
    this.loadPublicAnalyses();
  }

  // Load user's saved analyses from the server
  loadAnalyses = () => {
    if (this.state.auth.loggedIn) {
      return jwtFetch(`${DOMAINROOT}/api/user`)
        .then((data: ApiUser) => {
          this.setState({
            analyses: (data.analyses || [])
              .filter(x => !!x.status) // Ignore analyses with missing status
              .map(x => ApiToAppAnalysis(x))
          });
        })
        .catch(displayError);
    }
    return Promise.reject('You are not logged in');
  };

  // Load public analyses from the server
  loadPublicAnalyses = () =>
    fetch(`${DOMAINROOT}/api/analyses`)
      .then(response => response.json())
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
  checkAnalysesStatus = async () => {
    while (true) {
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
      await timeout(10000);
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
      loggingOut
    } = this.state.auth;

    const {
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
      </Modal>
    );

    const signupModal = () => (
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
      </Modal>
    );

    return (
      <Router>
        <div>
          {openLogin && loginModal()}
          {openReset && resetPasswordModal()}
          {openSignup && signupModal()}
          {openEnterResetToken && authActions.enterResetTokenModal()}
          <Layout>
           <Header>
             <Link to="/">Neuroscout</Link>
             <Menu
                theme="dark"
                mode="horizontal"
                defaultSelectedKeys={['2']}
                style={{ lineHeight: '64px' }}
              >
                <Menu.Item key="1">nav 1</Menu.Item>
                <Menu.Item key="2">nav 2</Menu.Item>
                <Menu.Item key="3">nav 3</Menu.Item>
              </Menu>
            </Header>
            <Row type="flex" justify="center"style={{ background: '#fff', padding: 0 }}>
                <Col xxl={{span: 14}} xl={{span: 16}} lg={{span: 18}} xs={{span: 24}} className="mainCol">
                  <div className="headerRow">
                    <div className="Login-col">
                    {this.state.auth.loggedIn
                      ? <span>
                          {`${email}`}
                          <Space />
                          <Button
                            onClick={(e) => {
                              return authActions.confirmLogout();
                            }}
                          >
                            Log out
                          </Button>
                        </span>
                      : <span>
                          <Button onClick={e => authActions.update({ openLogin: true })}>
                            Log in
                          </Button>
                          <Space />
                          <Button onClick={e => authActions.update({ openSignup: true })}>
                            Sign up
                          </Button>
                        </span>}
                    </div>
                    <h1>
                      <Link to="/">Neuroscout</Link>
                    </h1>
                    </div>
                  </Col>
              </Row>
            <Content style={{ background: '#fff' }}>
              <Route
                exact={true}
                path="/"
                render={props =>
                  <Home
                    analyses={analyses}
                    loggedIn={this.state.auth.loggedIn}
                    cloneAnalysis={this.cloneAnalysis}
                    onDelete={this.onDelete}
                  />}
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
                    return <AnalysisBuilder updatedAnalysis={() => this.loadAnalyses()} />;
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
                  />}
              />
              <Route
                exact={true}
                path="/browse/:id"
                render={props =>
                  <AnalysisBuilder
                    id={props.match.params.id}
                    updatedAnalysis={() => this.loadAnalyses()}
                  />
                }
              />

              <Route
                exact={true}
                path="/browse"
                render={props =>
                  <Browse analyses={publicAnalyses} cloneAnalysis={this.cloneAnalysis} />}
              />
            </Content>
          </Layout>
        </div>
      </Router>
    );
  }

  componentDidUpdate(prevProps, prevState) {
    // Need to do this so logout redirect only happens once, otherwise it'd be an infinite loop
    if (this.state.auth.loggingOut) authActions.update({ loggingOut: false });
    if ((prevState.auth.jwt !== this.state.auth.jwt)
      || (this.state.auth.loggedIn && this.state.loadAnalyses)) {
      this.loadAnalyses();
      this.checkAnalysesStatus();
      this.setState({loadAnalyses: false});
    }
  }
}

export default App;
