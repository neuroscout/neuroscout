import { Modal, message } from 'antd';
import Reflux from 'reflux';

var jwtDecode = require('jwt-decode');

import { authActions } from './auth.actions';
import { config } from './config';
import { AuthStoreState } from './coretypes';
import { displayError } from './utils';

const DOMAINROOT = config.server_url;

export class AuthStore extends Reflux.Store {

  constructor() {
    super();
    this.listenToMany(authActions);
    this.setState(this.getInitialState());
  }

  getInitialState() {
    let jwt = localStorage.getItem('jwt');
    try {
      let jwt_ob = jwtDecode(jwt);
      if (jwt_ob.exp * 1000 < Date.now()) {
        localStorage.removeItem('jwt');
        jwt = '';
      }
    } catch {
      jwt = '';
    }
    let _email = localStorage.getItem('email');
    let email = _email == null ? undefined : _email;
    return { auth: {
      jwt: jwt ? jwt : '',
      loggedIn: jwt ? true : false,
      nextURL: null,
      loginError: '',
      signupError: '',
      resetError: '',
      email: email,
      name: undefined,
      password: '',
      openLogin: false,
      openSignup: false,
      openReset: false,
      openEnterResetToken: false,
      loggingOut: false,
      token: null,
    }};
  }

  update(data: any) {
    let newAuth = this.state.auth;
    if (data) {
      for (let prop in data) {
        if (this.state.auth.hasOwnProperty(prop)) {
          newAuth[prop] = data[prop];
        }
      }
      this.setState({auth: newAuth});
    }
  }

  updateFromInput(name: keyof AuthStoreState, event: React.FormEvent<HTMLInputElement>) {
      const newState = {};
      if (event && event.currentTarget) {
        newState[name] = event.currentTarget.value;
        this.update(newState);
      }
  }

  // check to see if JWT is expired
  checkJWT(jwt) {
    if (jwt === undefined) {
      jwt = localStorage.getItem('jwt');
    }
    if (this.state.auth.loggedIn === false) { return false; }
    try {
      let jwt_ob = jwtDecode(jwt);
      if (jwt_ob.exp * 1000 < Date.now()) {
        localStorage.removeItem('jwt');
        this.update({jwt: '', loggedIn: false, openLogin: true});
        return false;
      }
      return true;
    } catch (e) {
        this.update({jwt: '', loggedIn: false, openLogin: true});
        return false;
    }
  }

  // Authenticate the user with the server. This function is called from login()
  authenticate(): Promise<string> {
    return new Promise((resolve, reject) => {
      const { email, password } = this.state.auth;
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
            this.update({ loginError: data.description || '' });
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
                message.success('Logged in.');
                localStorage.setItem('jwt', token);
                localStorage.setItem('email', email!);
                resolve(token);
              }
            }).catch(displayError);
          }}
        ).catch(displayError);
      });
    }

  // Log user in
  login = () => {
    const { email, password, loggedIn, openLogin, nextURL } = this.state;
    return this.authenticate()
      .then((jwt: string) => {
        this.update({
          jwt: jwt,
          password: '',
          loggedIn: true,
          openLogin: false,
          nextURL: null,
          loginError: ''
        });
      }).catch(displayError);
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
          this.update({
            signupError: errorMessage
          });
          throw new Error('Signup failed!');
        }
        this.update({ name, email, openSignup: false, signupError: '' });
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
    this.update({
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
      this.update({ openEnterResetToken: true, openReset: false });
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
        this.update({ openEnterResetToken: false});
        this.login();
      } else {
        response.json().then(json => ({ ... json }))
        .then((data: any) => {
          let errorMessage = '';
          Object.keys(data.message).forEach(key => {
            errorMessage += data.message[key];
          });
          that.update({resetError: errorMessage});
      });
    }
  })
    .catch(displayError);
  };
}
