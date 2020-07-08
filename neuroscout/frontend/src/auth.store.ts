import { Modal, message } from 'antd';
import Reflux from 'reflux';

var jwtDecode = require('jwt-decode');

import { api } from './api';
import { authActions } from './auth.actions';
import { config } from './config';
import { ApiUser, AuthStoreState, profileEditItems } from './coretypes';
import { displayError, jwtFetch } from './utils';

const domainRoot = config.server_url;

const localItems = ['email', 'avatar', 'isGAuth', ...profileEditItems];

export const setLocal = (auth: Partial<AuthStoreState>) => {
  localItems.map((x) => { localStorage.setItem(x, auth[x]); });
};

export const removeLocal = () => {
  [...localItems, 'jwt'].map((x) => { localStorage.removeItem(x); });
};

export const getLocal = () => {
  let ret = {};
  localItems.map((x) => { 
    let item = localStorage.getItem(x);
    item === null ? ret[x] = '' : ret[x] = item;
  });
  return ret;
};

export class AuthStore extends Reflux.Store {

  // jwt might not be set in state by the time getProfile is needed.
  // setState in this constructor doesn't take a callback...
  constructor() {
    super();
    this.listenToMany(authActions);
    this.state = this.getInitialState();
    if (!!this.state.auth.jwt) {
      this.getProfile();
    }
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

    let local: Partial<AuthStoreState> = getLocal();
    local.email === '' ? local.email = undefined : null;

    return { auth: {
      ...local,
      jwt: jwt ? jwt : '',
      loggedIn: jwt ? true : false,
      openTour: false,
      nextURL: null,
      loginError: '',
      signupError: '',
      resetError: '',
      password: '',
      openLogin: false,
      openSignup: false,
      openReset: false,
      openEnterResetToken: false,
      loggingOut: false,
      token: null,
      gAuth: null, 
      predictorCollections: jwt ? this.loadPredictorCollections() : []
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

  // jwtFetch response has already had .json() called on it compared to fetch call in authenticate 
  getProfile() {
    jwtFetch(`${domainRoot}/api/user`).then(response => {
      if (response.statusCode === 200) {
        this.update({institution: response.institution, name: response.name});
      }
    });
  }

  // Authenticate the user with the server. This function is called from login()
  authenticate(): Promise<string> {
    return new Promise((resolve, reject) => {
      let { email, password, avatar, isGAuth, name } = this.state.auth;
      let { accountconfirmError } = this;
      fetch(domainRoot + '/api/auth', {
        method: 'post',
        body: JSON.stringify({ email: isGAuth === true ? 'GOOGLE' : email, password: password }),
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
            let token = data.access_token;
            fetch(domainRoot + '/api/user', {
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

                response.json().then((user_data: ApiUser) => {
                  setLocal(user_data);
                  let profileItems: Partial<AuthStoreState> = {};
                  localItems.map((x) => profileItems[x] = user_data[x]);
                  this.update({ ...profileItems, openTour: user_data.first_login });
                  this.loadPredictorCollections(user_data);
                });
                return resolve(token);
              }
            }).catch(displayError);
          }}
        ).catch(displayError);
      });
    }

  loadPredictorCollections = (user?: ApiUser) => {
    (user ? Promise.resolve(user) : api.getUser()).then((_user: ApiUser): any => {
      if (_user && _user.predictor_collections) {
        let collections = _user.predictor_collections.map((x) => {
          return api.getPredictorCollection(x.id);
        });
        return Promise.all(collections);
      } else {
        return [];
      }
    }).then((collections) => {
      /* need to get dataset id from first predictor in each collection */
      collections.sort((a, b) => { return b.id - a.id; });
      this.update({predictorCollections: collections});
    });
  }

  // Log user in
  login = () => {
    return this.authenticate()
      .then((jwt: string) => {
        this.loadPredictorCollections();
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

  closeTour = () => {
    this.update({
      openTour: false
    });
  };

  launchTour = () => {
    this.update({
      openTour: true
    });
  };

  // Sign up for a new account
  signup() {
    const { name, email, password } = this.state.auth;
    fetch(domainRoot + '/api/user', {
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
  }

  // Log user out
  logout = () => {
    removeLocal();

    this.update({
      loggedIn: false,
      name: undefined,
      email: undefined,
      avatar: undefined,
      jwt: null,
      analyses: [],
      loggingOut: true,
      gAuth: null,
      institution: ''
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
    Modal.confirm({
      title: 'Account is not confirmed!',
      content: 'Your account has not been confirmed. \
        To continue, please follow the instructions sent to your email address.',
      okText: 'Resend confirmation',
      cancelText: 'Close',
      onOk() {
        fetch(domainRoot + '/api/user/resend_confirmation', {
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
    fetch(domainRoot + '/api/user/reset_password', {
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
    fetch(domainRoot + '/api/user/submit_token', {
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
