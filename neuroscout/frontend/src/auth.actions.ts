import Reflux from 'reflux';

var authActions = Reflux.createActions({
  'update': {},
  'jwtFetch': {sync: false, asyncResult: true},
  'authenticate': {sync: false, asyncResult: true},
  'login': {},
  'signUp': {},
  'confirmLogout': {},
  'resetPassword': {},
  'submitToken': {},
  'getInitialState': {},
  'updateFromInput': {}
});

export { authActions };
