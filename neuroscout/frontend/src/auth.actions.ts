import Reflux from 'reflux';

var authActions = Reflux.createActions({
  'update': {},
  'jwtFetch': {asyncResult: true},
  'authenticate': {asyncResult: true},
});

export { authActions };
