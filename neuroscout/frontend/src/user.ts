import { Modal, message } from 'antd';

var jwtDecode = require('jwt-decode');

import * as React from 'react';

import { api } from './api';
import { config } from './config';
import { ApiUser, ProfileState } from './coretypes';
import { displayError, jwtFetch } from './utils';

const domainRoot = config.server_url;

export const profileInit = () => {
  return {
    id: 0,
    name: '',
    user_name: '',
    picture: '',
    email: '',
    institution: '',
    orcid: '',
    bio: '',
    twitter_handle: '',
    personal_site: '',
    public_email: ''
  };
};

const localItems = ['isGAuth'];
const localProfileItems = Object.keys(profileInit());

export const setLocal = (user: Partial<UserStore>) => {
  localItems.map((x) => { localStorage.setItem(x, user[x]); });
  localProfileItems.filter(x => !!user.profile && x in user.profile)
                   .map((x) => { localStorage.setItem(x, user.profile![x]); });
};

export const removeLocal = () => {
  localStorage.clear();
};

export const getLocal = () => {
  let userItems = {};
  let profileItems = {};
  localItems.map((x) => {
    let item = localStorage.getItem(x);
    item === null ? userItems[x] = '' : userItems[x] = item;
  });
  localProfileItems.map((x) => {
    let item = localStorage.getItem(x);
    item === null ? profileItems[x] = '' : profileItems[x] = item;
  });
  return [userItems, profileItems];
};

export class UserStore {

  constructor(setState) {
    this.setState = setState;
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

    this.jwt = jwt ? jwt : '';
    this.loggedIn = jwt ? true : false;
    this.openTour = false;
    this.nextURL = null;
    this.loginError = '';
    this.signupError = '';
    this.resetError = '';
    this.password = '';
    this.openLogin = false;
    this.openSignup = false;
    this.openReset = false;
    this.openEnterResetToken = false;
    this.loggingOut = false;
    this.token = null;
    this.gAuth = null;
    this.isGAuth = false;
    this.predictorCollections = [];
    this.profile = {
      ...profileInit(),
      update: (updates: Partial<ProfileState>, updateLocal: boolean = false) => {
        this.update({ profile: { ...this.profile, ...updates } }, updateLocal);
      }
    };
    const [userItems, profileItems] = getLocal();
    this.update(userItems);
    this.profile.update(profileItems);
  }
  jwt;
  loggedIn;
  openTour;
  nextURL;
  loginError;
  signupError;
  resetError;
  password;
  openLogin;
  openSignup;
  openReset;
  openEnterResetToken;
  loggingOut;
  token;
  gAuth;
  isGAuth?;
  predictorCollections;
  profile: ProfileState;
  setState: (any) => void;

  update = (data: any, updateLocal: boolean = false) => {
    if (data) {
      for (let prop in data) {
        if (this.hasOwnProperty(prop)) {
          this[prop] = data[prop];
        }
      }
      this.setState({ user: this });
      if (updateLocal) {
        setLocal(this);
      }
    }
  };

  updateFromInput = (
     name: keyof (UserStore & ProfileState),
     event: React.FormEvent<HTMLInputElement>,
     profile: boolean = false
  ) => {
    const newState = {};
    if (event && event.currentTarget) {
      newState[name] = event.currentTarget.value;
      if (profile) {
        this.profile.update(newState);
      } else {
        this.update(newState);
      }
    }
  };

  // check to see if JWT is expired
  checkJWT = (jwt) => {
    if (jwt === undefined) {
      jwt = localStorage.getItem('jwt');
    }
    if (this.loggedIn === false) { return false; }
    try {
      let jwt_ob = jwtDecode(jwt);
      if (jwt_ob.exp * 1000 < Date.now()) {
        localStorage.removeItem('jwt');
        this.update({ jwt: '', loggedIn: false, openLogin: true });
        return false;
      }
      return true;
    } catch (e) {
      this.update({ jwt: '', loggedIn: false, openLogin: true });
      return false;
    }
  };

  // Authenticate the user with the server. This function is called from login()
  authenticate = (): Promise<string> => {
    return new Promise((resolve, reject) => {
      let { password, isGAuth, accountconfirmError } = this;
      let { email, name, picture } = this.profile;
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
                  response.json().then((missing_data: { message: string }) => {
                    if (missing_data.message === 'Your account has not been confirmed.') {
                      accountconfirmError(token);
                    }
                    reject('Authentication failed');
                  });

                } else {
                  message.success('Logged in.');

                  localStorage.setItem('jwt', token);

                  response.json().then((user_data: ApiUser) => {
                    let profileItems: Partial<ProfileState> = {};
                    localProfileItems.map((x) => profileItems[x] = user_data[x]);
                    this.update({ openTour: user_data.first_login });
                    this.profile.update(profileItems, true);
                    this.loadPredictorCollections(user_data);
                  });
                  return resolve(token);
                }
              }).catch(displayError);
          }
        }
        ).catch(displayError);
    });
  }

  loadPredictorCollections = (user?: ApiUser) => {
    api.getPredictorCollections().then(colls => {
      this.update({predictorCollections: colls});
    });
  };

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
  signup = (newUser: {password: string, name: string, email: string}) => {
    const { name, email, password } = newUser;
    this.update({password: password});  
    this.profile.update({name: name, email: email});
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
          if (Object.keys(data.message).length === 0) {
            throw new Error('Signup failed!');
          }
          return;
        }
        this.update({ openSignup: false, signupError: '' });
        this.profile.update({ name: name, email: email, user_name: data.user_name });
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
    removeLocal();

    this.update({
      loggedIn: false,
      jwt: null,
      analyses: [],
      loggingOut: true,
      gAuth: null,
      isGAuth: false
    });
    this.profile.update(profileInit());
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
      }
    });
  };

  // Reset password function
  resetPassword = (): void => {
    const { email } = this.profile;
    fetch(domainRoot + '/api/user/reset_password', {
      method: 'post',
      body: JSON.stringify({ email: email }),
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
    const { token, password } = this;
    const that = this;
    fetch(domainRoot + '/api/user/submit_token', {
      method: 'post',
      body: JSON.stringify({ token: token, password: password }),
      headers: {
        'Content-type': 'application/json'
      }
    })
      .then((response) => {
        if (response.ok) {
          this.update({ openEnterResetToken: false });
          this.login();
        } else {
          response.json().then(json => ({ ...json }))
            .then((data: any) => {
              let errorMessage = '';
              Object.keys(data.message).forEach(key => {
                errorMessage += data.message[key];
              });
              that.update({ resetError: errorMessage });
            });
        }
      })
      .catch(displayError);
  };
}
