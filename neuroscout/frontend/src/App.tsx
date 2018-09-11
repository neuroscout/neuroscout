/*
Top-level App component containing AppState. The App component is currently responsible for:
- Authentication (signup, login and logout)
- Routing
- Managing user's saved analyses (list display, clone and delete)
*/
import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Modal, Icon, Input, Form, message } from 'antd';
import { displayError, jwtFetch, timeout } from './utils';
import { Space } from './HelperComponents';
import { ApiUser, ApiAnalysis, AppAnalysis } from './coretypes';
import Home from './Home';
import AnalysisBuilder from './Builder';
import Browse from './Browse';
import { BrowserRouter as Router, Route, Link, Redirect } from 'react-router-dom';
import './App.css';
import { config } from './config';

const FormItem = Form.Item;
const DOMAINROOT = config.server_url;
const { localStorage } = window;

const { Footer, Content, Header } = Layout;

interface AppState {
  loggedIn: boolean;
  openLogin: boolean;
  openSignup: boolean;
  openReset: boolean;
  openEnterResetToken: boolean;
  loginError: string;
  signupError: string;
  resetError: string;
  email: string | undefined;
  name: string | undefined;
  password: string | undefined;
  token: string | null;
  jwt: string | null;
  nextURL: string | null; // will probably remove this and find a better solution to login redirects
  analyses: AppAnalysis[]; // List of analyses belonging to the user
  publicAnalyses: AppAnalysis[]; // List of public analyses
  loggingOut: boolean; // flag set on logout to know to redirect after logout
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
class App extends React.Component<{}, AppState> {
  constructor(props) {
    super(props);
    const jwt = localStorage.getItem('jwt');
    let _email = localStorage.getItem('email');
    let email = _email == null ? undefined : _email;
    this.state = {
      loggedIn: !!jwt,
      openLogin: false,
      openSignup: false,
      openReset: false,
      openEnterResetToken: false,
      loginError: '',
      signupError: '',
      resetError: '',
      email: email,
      name: undefined,
      jwt: jwt,
      password: '',
      nextURL: null,
      analyses: [],
      publicAnalyses: [],
      loggingOut: false,
      token: null
    };
    if (jwt) {
      this.loadAnalyses();
      this.checkAnalysesStatus();
    }
    this.loadPublicAnalyses();
  }

  // Load user's saved analyses from the server
  loadAnalyses = () => {
    if (this.state.jwt) {
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

  // Authenticate the user with the server. This function is called from login()
  authenticate = () =>
    new Promise((resolve, reject) => {
      const { email, password } = this.state;
      const { accountconfirmError } = this;
      fetch(DOMAINROOT + '/api/auth', {
        method: 'post',
        body: JSON.stringify({ email: email, password: password }),
        headers: {
          'Content-type': 'application/json'
        }
      })
        .then(response => response.json())
        .then((data: { status_code: number; access_token?: string; description?: string }) => {
          if (data.status_code === 401) {
            this.setState({ loginError: data.description || '' });
            reject('Authentication failed');
          } else if (data.access_token) {
            const token = data.access_token;
            fetch(DOMAINROOT + '/api/user', {
              method: 'get',
              headers: {
                'Content-type': 'application/json',
                'authorization': 'JWT ' + data.access_token
              }
            })
            .then((response) => {
              if (response.status === 401) {
                response.json().then((missing_data: {message: string}) => {
                  if (missing_data.message === 'Your account has not been confirmed.') {
                    accountconfirmError(token);
                  }
                  reject('Authentication failed');
                });

              } else {
                localStorage.setItem('jwt', token);
                localStorage.setItem('email', email!);
                resolve(token);
              }
            }).catch(displayError);
          }}
        ).catch(displayError);
      });

  // Log user in
  login = () => {
    const { email, password, loggedIn, openLogin, nextURL } = this.state;
    return this.authenticate()
      .then((jwt: string) => {
        this.setState({
          jwt: jwt,
          password: '',
          loggedIn: true,
          openLogin: false,
          nextURL: null,
          loginError: ''
        });
      })
      .then(() => this.loadAnalyses())
      .catch(displayError);
  };

  // Sign up for a new account
  signup = () => {
    const { name, email, password, openSignup } = this.state;
    fetch(DOMAINROOT + '/api/user', {
      method: 'post',
      body: JSON.stringify({ email: email, password: password, name: name }),
      headers: {
        'Content-type': 'application/json'
      }
    })
      .then(response => response.json().then(json => ({ ...json, statusCode: response.status })))
      .then((data: any) => {
        if (data.statusCode !== 200) {
          let errorMessage = '';
          Object.keys(data.message).forEach(key => {
            errorMessage += data.message[key];
          });
          this.setState({
            signupError: errorMessage
          });
          throw new Error('Signup failed!');
        }
        this.setState({ name, email, openSignup: false, signupError: '' });
        Modal.success({
          title: 'Account created!',
          content: 'Your account has been sucessfully created. \
          You will receive a confirmation email shortly. Please follow the instructions to activate your account\
          and start using Neuroscout. ',
          okText: 'Okay',
        });
      })
      .catch(displayError);
  };

  // Log user out
  logout = () => {
    localStorage.removeItem('jwt');
    localStorage.removeItem('email');
    this.setState({
      loggedIn: false,
      name: undefined,
      email: undefined, jwt: null,
      analyses: [],
      loggingOut: true
    });
  };

  // Display modal to confirm logout
  confirmLogout = (): void => {
    const that = this;
    Modal.confirm({
      title: 'Are you sure you want to log out?',
      content: 'If you have any unsaved changes they will be discarded.',
      okText: 'Yes',
      cancelText: 'No',
      onOk() {
        that.logout();
      }
    });
  };

  // Display modal to resend confirmation link
  accountconfirmError = (jwt): void => {
    const that = this;
    Modal.confirm({
      title: 'Account is not confirmed!',
      content: 'Your account has not been confirmed. \
        To continue, please follow the instructions sent to your email address.',
      okText: 'Resend confirmation',
      cancelText: 'Close',
      onOk() {
        fetch(DOMAINROOT + '/api/user/resend_confirmation', {
          method: 'post',
          headers: {
            'Content-type': 'application/json',
            'authorization': 'JWT ' + jwt
          }
        })
        .catch(displayError);
      },
    });
  };

  // Reset password function
  resetPassword = (): void => {
    const { email } = this.state;
    fetch(DOMAINROOT + '/api/user/reset_password', {
      method: 'post',
      body: JSON.stringify({ email: email}),
      headers: {
        'Content-type': 'application/json'
      }
    })
    .catch(displayError)
    .then(() => {
      this.setState({ openEnterResetToken: true, openReset: false });
    });
  };

  // Reset password function
  submitToken = (): void => {
    const { token, password } = this.state;
    const that = this;
    fetch(DOMAINROOT + '/api/user/submit_token', {
      method: 'post',
      body: JSON.stringify({ token: token, password: password}),
      headers: {
        'Content-type': 'application/json'
      }
    })
    .then((response) =>  {
      if (response.ok) {
        this.setState({ openEnterResetToken: false});
        this.login();
      } else {
        response.json().then(json => ({ ... json }))
        .then((data: any) => {
          let errorMessage = '';
          Object.keys(data.message).forEach(key => {
            errorMessage += data.message[key];
          });
          that.setState({resetError: errorMessage});
      });
    }
  })
    .catch(displayError);
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
      analyses,
      publicAnalyses,
      loggingOut
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
          this.setState({ openReset: false });
        }}
      >
        <p>
         Please enter an email address to send reset instructions
        </p>
        <Form
          onSubmit={e => {
            e.preventDefault();
            this.resetPassword();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="mail" style={{ fontSize: 13 }}/>}
              placeholder="Email"
              type="email"
              size="large"
              value={email}
              onChange={this.setStateFromInput('email')}
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
          this.setState({ openEnterResetToken: false });
        }}
      >
        <p>
         We have sent a reset token to {email} <br/>
         Please enter the token below, along with a new password for the account.
       </p>
        <Form
          onSubmit={e => {
            e.preventDefault();
            this.submitToken();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="tags" style={{ fontSize: 13 }}/>}
              placeholder="Token"
              type="token"
              size="large"
              onChange={this.setStateFromInput('token')}
            />
          </FormItem>
          <FormItem>
            <Input
              prefix={<Icon type="lock" style={{ fontSize: 13 }}/>}
              placeholder="Password"
              type="password"
              size="large"
              onChange={this.setStateFromInput('password')}
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
        visible={openLogin}
        footer={null}
        maskClosable={true}
        onCancel={e => {
          this.setState({ openLogin: false });
        }}
      >
        <p>
          {loginError ? loginError : ''}
        </p>
        <br />
        <Form
          onSubmit={e => {
            e.preventDefault();
            this.login();
          }}
        >
          <FormItem>
            <Input
              prefix={<Icon type="mail" style={{ fontSize: 13 }}/>}
              placeholder="Email"
              type="email"
              size="large"
              value={email}
              onChange={this.setStateFromInput('email')}
            />
          </FormItem>
          <FormItem>
            <Input
              prefix={<Icon type="lock" style={{ fontSize: 13 }}/>}
              placeholder="Password"
              type="password"
              value={password}
              onChange={this.setStateFromInput('password')}
            />
          </FormItem>
          <FormItem>
           <a onClick={e => {this.setState( { openLogin: false, openReset: true}); }}>Forgot password</a><br/>
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
        onCancel={e => {
          this.setState({ openSignup: false });
        }}
      >
        <p>
          {signupError}
        </p>
        <br />
        <Form
          onSubmit={e => {
            e.preventDefault();
            this.signup();
          }}
        >
          <FormItem>
            <Input
              placeholder="Full name"
              size="large"
              value={name}
              onChange={this.setStateFromInput('name')}
            />
          </FormItem>
          <FormItem>
            <Input
              placeholder="Email"
              type="email"
              size="large"
              value={email}
              onChange={this.setStateFromInput('email')}
            />
          </FormItem>
          <FormItem>
            <Input
              placeholder="Password"
              type="password"
              value={password}
              onChange={this.setStateFromInput('password')}
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
          {openEnterResetToken && enterResetTokenModal()}
          <Layout>
            <div className="headerRow">
            <Row type="flex" justify="center"style={{ background: '#fff', padding: 0 }}>
                  <Col lg={{span: 9}} xs={{span: 12}}>
                    <h1>
                      <Link to="/">Neuroscout</Link>
                    </h1>
                  </Col>
                  <Col lg={{span: 9}} xs={{span: 12}}>
                    <div className="Login-col">
                    {loggedIn
                      ? <span>
                          {`${email}`}
                          <Space />
                          <Button onClick={e => this.confirmLogout()}>Log out</Button>
                        </span>
                      : <span>
                          <Button onClick={e => this.setState({ openLogin: true })}>
                            Log in
                          </Button>
                          <Space />
                          <Button onClick={e => this.setState({ openSignup: true })}>
                            Sign up
                          </Button>
                        </span>}
                    </div>
                  </Col>
              </Row>
              </div>
            <Content style={{ background: '#fff' }}>
              <Route
                exact={true}
                path="/"
                render={props =>
                  <Home
                    analyses={analyses}
                    loggedIn={loggedIn}
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
                  if (loggedIn) {
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

  componentDidUpdate() {
    // Need to do this so logout redirect only happens once, otherwise it'd be an infinite loop
    if (this.state.loggingOut) this.setState({ loggingOut: false });
  }
}

export default App;
