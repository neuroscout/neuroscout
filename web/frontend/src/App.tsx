/* 
Top-level App component containing AppState. The App component is currently responsible for:
- Authentication (signup, login and logout)
- Routing
- Managing user's saved analyses (list display, clone and delete)
*/
import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Modal, Input, Form, message } from 'antd';
import { displayError, jwtFetch } from './utils';
import { Space } from './HelperComponents';
import { ApiUser, ApiAnalysis, AppAnalysis } from './coretypes';
import Home from './Home';
import AnalysisBuilder from './Builder';
import Browse from './Browse';
import { BrowserRouter as Router, Route, Link, Redirect } from 'react-router-dom';
import './App.css';

const FormItem = Form.Item;
const DOMAINROOT = 'http://localhost:80';
const { localStorage } = window;

const { Footer, Content, Header } = Layout;

interface AppState {
  loggedIn: boolean;
  openLogin: boolean;
  openSignup: boolean;
  loginError: string;
  signupError: string;
  email: string | null;
  name: string | null;
  password: string | null;
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
    const email = localStorage.getItem('email');
    this.state = {
      loggedIn: !!jwt,
      openLogin: false,
      openSignup: false,
      loginError: '',
      signupError: '',
      email: email || 'test2@test.com', // For development - remove test2@test.com later
      name: null,
      jwt: jwt,
      password: 'password', // For development - set to '' in production
      nextURL: null,
      analyses: [],
      publicAnalyses: [],
      loggingOut: false
    };
    if (jwt) this.loadAnalyses();
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

  // Authenticate the user with the server. This function is called from login()
  authenticate = () =>
    new Promise((resolve, reject) => {
      const { email, password } = this.state;
      fetch(DOMAINROOT + '/api/auth', {
        method: 'post',
        body: JSON.stringify({ email: email, password: password }),
        headers: {
          'Content-type': 'application/json'
        }
      })
        .then(response => response.json())
        .then((data: { status_code: number; access_token?: string; description?: string }) => {
          if (data.access_token) {
            message.success('Authentication successful');
            localStorage.setItem('jwt', data.access_token);
            localStorage.setItem('email', email!);
            resolve(data.access_token);
          } else if (data.status_code === 401) {
            this.setState({ loginError: data.description || '' });
            reject('Authentication failed');
          }
        })
        .catch(displayError);
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

  // Sign up for a new account and if successful, immediately log the user in
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
        message.success('Signup successful');
        const { name, email, password } = data;
        this.setState({ name, email, openSignup: false, signupError: '' });
      })
      .then(() => this.login())
      .catch(displayError);
  };

  // Log user out
  logout = () => {
    localStorage.removeItem('jwt');
    localStorage.removeItem('email');
    this.setState({
      loggedIn: false,
      name: null,
      email: null,
      jwt: null,
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
    if (analysis.status && analysis.status !== 'DRAFT') {
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
      openLogin,
      openSignup,
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
    const loginModal = () =>
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
          {loginError ? loginError : 'For development try "test2@test.com" and "password"'}
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
            <Button style={{ width: '100%' }} htmlType="submit" type="primary">
              Log in
            </Button>
          </FormItem>
        </Form>
      </Modal>;
    const signupModal = () =>
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
      </Modal>;
    return (
      <Router>
        <div>
          {openLogin && loginModal()}
          {openSignup && signupModal()}
          <Layout>
            <Header style={{ background: '#fff', padding: 0 }}>
              <Row type="flex" justify="center">
                <Col span={18}>
                  <Row type="flex" justify="space-between">
                    <Col span={12}>
                      <h1>
                        <Link to="/">Neuroscout</Link>
                      </h1>
                    </Col>
                    <Col span={6}>
                      {loggedIn
                        ? <span>
                            {`Logged in as ${email}`}
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
                    </Col>
                  </Row>
                </Col>
              </Row>
            </Header>
            <Content style={{ background: '#fff' }}>
              <Route
                exact
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
                exact
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
                exact
                path="/browse"
                render={props =>
                  <Browse analyses={publicAnalyses} cloneAnalysis={this.cloneAnalysis} />}
              />
            </Content>
            <Footer style={{ background: '#fff' }}>
              <Row type="flex" justify="center">
                <Col span={4}>
                  <br />
                  <p>Neuroscout - Copyright 2017</p>
                </Col>
              </Row>
            </Footer>
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
