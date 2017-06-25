import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Modal, Input, Form, message } from 'antd';
import { displayError, jwtFetch, Space } from './utils';
import { ApiUser, ApiAnalysis, AppAnalysis } from './commontypes';
import Home from './Home';
import AnalysisBuilder from './Builder';
import Browse from './Browse';
import {
  BrowserRouter as Router,
  Route, Link, Redirect
} from 'react-router-dom';
import './App.css';

const FormItem = Form.Item;
const DOMAINROOT = 'http://localhost:80';
const { localStorage } = window;

const { Footer, Content, Header } = Layout;

interface AppState {
  loggedIn: boolean;
  openLogin: boolean;
  openSignup: boolean;
  email: string | null;
  name: string | null;
  password: string | null;
  jwt: string | null;
  nextURL: string | null; // will probably remove this and find a better solution to login redirects
  analyses: AppAnalysis[];
  publicAnalyses: AppAnalysis[];
}

const ApiToAppAnalysis = (data: ApiAnalysis): AppAnalysis => (
  {
    id: data.hash_id!,
    name: data.name,
    description: data.description,
    status: data.status,
    modifiedAt: data.modified_at
  }
);

class App extends React.Component<{}, AppState>{
  constructor(props) {
    super(props);
    // window.localStorage.clear()
    const jwt = localStorage.getItem('jwt');
    const email = localStorage.getItem('email');
    this.state = {
      loggedIn: !!jwt,
      openLogin: false,
      openSignup: false,
      email: email || 'test2@test.com',  // For development - remove test2@test.com later
      name: null,
      jwt: jwt,
      password: 'password', // For development - set to '' in production
      nextURL: null,
      analyses: [],
      publicAnalyses: [],
    };
    if (jwt) this.loadAnalyses();
    this.loadPublicAnalyses();
  }

  loadAnalyses = () => {
    if (this.state.jwt) {
      return jwtFetch(`${DOMAINROOT}/api/user`)
        .then(response => response.json())
        .then((data: ApiUser) => {
          this.setState({
            analyses: data.analyses
              .filter(x => !!x.status)  // Ignore analyses with missing status
              .map(x => ApiToAppAnalysis(x))
          });
        })
        .catch(displayError);
    }
    return Promise.reject('You are not logged in');
  }

  loadPublicAnalyses = () => fetch(`${DOMAINROOT}/api/analyses`)
    .then(response => response.json())
    .then((data: ApiAnalysis[]) => {
      this.setState({
        publicAnalyses: data
          .filter(x => !!x.status)  // Ignore analyses with missing status
          .map(x => ApiToAppAnalysis(x))
      });
    })
    .catch(displayError);

  authenticate = () => new Promise((resolve, reject) => {
    const { email, password } = this.state;
    fetch(DOMAINROOT + '/api/auth', {
      method: 'post',
      body: JSON.stringify({ email: email, password: password }),
      headers: {
        'Content-type': 'application/json'
      }
    })
      .then(response => response.json())
      .then((data: { access_token: string }) => {
        if (data.access_token) {
          message.success('Authentication successful');
          localStorage.setItem('jwt', data.access_token);
          localStorage.setItem('email', email!);
          resolve(data.access_token);
        } else {
          reject('Authentication failed');
        }
      })
      .catch(displayError);
  });

  login = () => {
    const { email, password, loggedIn, openLogin, nextURL } = this.state;
    return this.authenticate()
      .then((jwt: string) => {
        this.setState({
          jwt: jwt, password: '', loggedIn: true, openLogin: false, nextURL: null
        });
      })
      .then(() => this.loadAnalyses())
      .catch(displayError);
  }

  signup = () => {
    const { name, email, password, openSignup } = this.state;
    fetch(DOMAINROOT + '/api/user', {
      method: 'post',
      body: JSON.stringify({ email: email, password: password, name: name }),
      headers: {
        'Content-type': 'application/json'
      }
    })
      .then((response) => {
        if (response.status !== 200) {
          throw 'Sign up failed';
        }
        response.json().then((data: any) => {
          message.success('Signup successful');
          const { name, email, password } = data;
          this.setState({ name, email, openSignup: false });
          return this.authenticate();
        });
      })
      .then(() => message.success('Logged in'))
      .then(() => this.loadAnalyses())
      .catch(displayError);
  }

  logout = () => {
    localStorage.removeItem('jwt');
    localStorage.removeItem('email');
    this.setState({ loggedIn: false, email: null, jwt: null, analyses: [] });
  }

  setStateFromInput = (name: keyof AppState) => (event: React.FormEvent<HTMLInputElement>) => {
    const newState = {};
    newState[name] = event.currentTarget.value;
    this.setState(newState);
  }

  deleteAnalysis = (id): void => {
    jwtFetch(`${DOMAINROOT}/api/analyses/${id}`, { method: 'delete' })
      .then(response => {
        if (response.status !== 200) {
          throw 'Something went wrong - most likely the analysis is not locked. Will fix it later';
        }
        return response.json()
      })
      .then((data: ApiAnalysis) => {
        this.setState({ analyses: this.state.analyses.filter(a => a.id !== id) });
      })
      .catch(displayError);
  }

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
      },
    });
  }

  cloneAnalysis = (id): void => {
    jwtFetch(`${DOMAINROOT}/api/analyses/${id}/clone`, { method: 'post' })
      .then(response => {
        if (response.status !== 200) {
          throw 'Something went wrong - most likely the analysis is not locked. Will fix it later';
        }
        return response.json()
      })
      .then((data: ApiAnalysis) => {
        const analysis = ApiToAppAnalysis(data)
        this.setState({ analyses: this.state.analyses.concat([analysis]) });
      })
      .catch(displayError);
  }

  // loginAndNavigate = (nextURL: string) => {
  //   if (this.state.loggedIn) {
  //     document.location.href = nextURL;
  //     return;
  //   }
  //   this.setState({ openLogin: true, nextURL });
  // }

  // ensureLoggedIn = () => new Promise((resolve, reject) => {
  //   if (this.state.loggedIn) {
  //     resolve();
  //   } else {
  //     this.setState({ openLogin: true });
  //     this.login().then(() => resolve()).catch(() => reject());
  //   }
  // });

  render() {
    const { loggedIn, email, name, openLogin, openSignup, password, analyses, publicAnalyses } = this.state;
    const loginModal = () => (
      <Modal
        title="Log into Neuroscout"
        visible={openLogin}
        footer={null}
        maskClosable={true}
        onCancel={e => { this.setState({ openLogin: false }); }}
      >
        <p>{'For development try "test2@test.com" and "password"'}</p><br />
        <Form>
          <FormItem>
            <Input placeholder="Email"
              type="email"
              size="large"
              value={email}
              onChange={this.setStateFromInput('email')}
            />
          </FormItem>
          <FormItem>
            <Input placeholder="Password"
              type="password"
              value={password}
              onChange={this.setStateFromInput('password')}
            />
          </FormItem>
          <FormItem>
            <Button
              style={{ width: '100%' }}
              type="primary"
              onClick={e => { this.login(); }}
            >Log in</Button>
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
        onCancel={e => { this.setState({ openSignup: false }); }}
      >
        <Form>
          <FormItem>
            <Input placeholder="Full name"
              size="large"
              value={name}
              onChange={this.setStateFromInput('name')}
            />
          </FormItem>
          <FormItem>
            <Input placeholder="Email"
              type="email"
              size="large"
              value={email}
              onChange={this.setStateFromInput('email')}
            />
          </FormItem>
          <FormItem>
            <Input placeholder="Password"
              type="password"
              value={password}
              onChange={this.setStateFromInput('password')}
            />
          </FormItem>
          <FormItem>
            <Button
              style={{ width: '100%' }}
              type="primary"
              onClick={e => { this.signup(); }}
            >Sign up</Button>
          </FormItem>
        </Form>
      </Modal>
    );
    return (
      <Router>
        <div>
          {openLogin && loginModal()}
          {openSignup && signupModal()}
          <Layout>
            <Header style={{ background: '#fff', padding: 0 }}>
              <Row type="flex" justify="center">
                <Col span={10}>
                  <h1><Link to="/">Neuroscout</Link></h1>
                </Col>
                <Col span={6}>
                  {loggedIn ?
                    (
                      <span>{`Logged in as ${email}`}
                        <Space />
                        <Button onClick={e => this.logout()}>Log out</Button>
                      </span>
                    ) :
                    (
                      <span>
                        <Button onClick={e => this.setState({ openLogin: true })}>Log in</Button>
                        <Button onClick={e => this.setState({ openSignup: true })}>Sign up</Button>
                      </span>
                    )
                  }
                </Col>
              </Row>
            </Header>
            <Content style={{ background: '#fff' }}>
              <Route exact path="/" render={(props) =>
                <Home
                  analyses={analyses}
                  loggedIn={loggedIn}
                  cloneAnalysis={this.cloneAnalysis}
                  onDelete={this.onDelete}
                />}
              />
              <Route exact path="/builder" render={(props) =>
                <AnalysisBuilder updatedAnalysis={() => this.loadAnalyses()} />} />
              <Route path="/builder/:id" render={(props) =>
                <AnalysisBuilder id={props.match.params.id} updatedAnalysis={() => this.loadAnalyses()} />} />
              <Route exact path="/browse" render={
                (props) => <Browse
                  analyses={publicAnalyses}
                  cloneAnalysis={this.cloneAnalysis}
                />
              }
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
      </Router >
    );
  }
}

export default App;
