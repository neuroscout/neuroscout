import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Modal, Input, Form, message } from 'antd';
import { displayError } from './utils';

const FormItem = Form.Item;
const DOMAINROOT = 'http://localhost:80';
const { localStorage } = window;

import {
  BrowserRouter as Router,
  Route, Link, Redirect
} from 'react-router-dom';

import './App.css';

import { Home } from './Home';
import { AnalysisBuilder } from './Builder';

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
}

const Browse = () => (
  <Row type="flex" justify="center">
    <Col span={16}>
      <h2>Browser Public Analyses</h2>
    </Col>
  </Row>
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
      nextURL: null
    };
  }

  authenticate = () => new Promise((resolve, reject) => {
    const { email, password } = this.state;
    fetch(DOMAINROOT + '/api/auth', {
      method: 'post',
      body: JSON.stringify({ email: email, password: password }),
      headers: {
        'Content-type': 'application/json'
      }
    })
      .then((response) => {
        response.json().then((data: { access_token: string }) => {
          if (data.access_token) {
            message.success('Authentication successful');
            localStorage.setItem('jwt', data.access_token);
            localStorage.setItem('email', email!);
            resolve(data.access_token);
          } else {
            reject('Authentication failed');
          }
        });
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
      .catch(displayError);
  }

  logout = () => {
    localStorage.removeItem('jwt');
    localStorage.removeItem('email');
    this.setState({ loggedIn: false, email: null, jwt: null });
  }

  setStateFromInput = (name: keyof AppState) => (event: React.FormEvent<HTMLInputElement>) => {
    const newState = {};
    newState[name] = event.currentTarget.value;
    this.setState(newState);
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
    const { loggedIn, email, name, openLogin, openSignup, password } = this.state;
    const loginModal = () => (
      <Modal
        title="Log into Neuroscout"
        visible={openLogin}
        footer={null}
        maskClosable={true}
        onCancel={e => { this.setState({ openLogin: false }); }}
      >
        <p>{"For development try 'test2@test.com' and 'password'"}</p><br />
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
                  <h1><a href="/">Neuroscout</a></h1>
                </Col>
                <Col span={6}>
                  {loggedIn ?
                    <span>{`Logged in as ${email}`}
                      <Button onClick={e => this.logout()}>Log out</Button>
                    </span> :
                    <span>
                      <Button onClick={e => this.setState({ openLogin: true })}>Log in</Button>
                      <Button onClick={e => this.setState({ openSignup: true })}>Sign up</Button>
                    </span>
                  }
                </Col>
              </Row>
            </Header>
            <Content style={{ background: '#fff' }}>
              <Route exact path="/" render={(props) => <Home />} />
              <Route path="/builder" render={(props) => <AnalysisBuilder />} />
              <Route exact path="/browse" component={Browse} />
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

const init = () => {
  // window.localStorage.clear(); // Dev-only, will remove later once there is user/password prompt functionality
};

init();
export default App;
