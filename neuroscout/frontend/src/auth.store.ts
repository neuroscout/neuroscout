import { Modal, message } from 'antd';
import Reflux from 'reflux';

import { authActions } from './auth.actions';
import { config } from './config';
import { displayError } from './utils';

const DOMAINROOT = config.server_url;

/*
export class AuthStore extends Reflux.Store {
    Actions = authActions;
    // typescript just relax okay?
    // setState: any;
    // listen: any;
    state = {
        counter: 0
    };

    constructor() {
      super();
      this.state = {counter: 0};
      // tslint:disable-next-line:no-console
      console.log(this.state);
    }

    onIncrementSomething() {
        this.setState({
            counter: ++this.state.counter
        });
    }
}
*/

export class AuthStore extends Reflux.Store {
  constructor() {
    super();
    let jwt = localStorage.getItem('jwt');
    this.setState({auth: {jwt: jwt ? jwt : ''}});
  }

  auth = {};

  update(data) {
    // tslint:disable-next-line:no-console
    console.log(data);
    if (data) {
      for (let prop in data) {
        if (data.hasownProperty(prop)) {
          this.auth[prop] = data[prop];
        }
      }
      this.trigger(this.auth);
    }
  }

  // Wrapper around the standard 'fetch' that takes care of:
  // - Adding jwt to request header
  // - Decoding JSON response and adding the response status code to decoded JSON object
  async jwtFetch(path: string, options?: object) {
    const jwt = window.localStorage.getItem('jwt');
    if (jwt === null) {
      const error = 'JWT not found in local storage. You must be logged in.';
      message.error(error);
    }
    const newOptions = {
      ...options,
      headers: {
        'Content-type': 'application/json',
        Authorization: 'JWT ' + jwt
      }
    };
    let response = await fetch(path, newOptions);
    if (response.status !== 401) {
      
    }
    if (response.status !== 200) {
      displayError(new Error(`HTTP ${response.status} on ${path}`));
    }
    let copy = await fetch(path, newOptions).then(_response => {
      return _response.json().then(json => {
        // Always add statusCode to the data object or array returned by response.json()
        let _copy: any;
        if ('length' in json) {
          // array
          _copy = [...json];
          (_copy as any).statusCode = _response.status;
        } else {
          // object
          _copy = { ...json, statusCode: _response.status };
        }
        return _copy;
      });
      return copy;
    });
  }

  // Authenticate the user with the server. This function is called from login()
  authenticate() {
    new Promise((resolve, reject) => {
      const { email, password } = this.state.data;
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
  }
}
