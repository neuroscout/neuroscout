import Reflux from 'reflux';

var authActions = Reflux.createActions({
  'update': {},
  'jwtFetch': {sync: false, asyncResult: true},
  'authenticate': {sync: false, asyncResult: true},
  'login': {},
  'logout': {},
  'signup': {},
  'confirmLogout': {},
  'resetPassword': {},
  'submitToken': {},
  'getInitialState': {},
  'updateFromInput': {},
  'checkJWT': {}
});

export { authActions };
