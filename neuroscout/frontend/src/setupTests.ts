/*
Jest (the test runner) runs this file first before running any of the test suites.
Create mock matchMedia and localStorage for the tests to work.
*/
import { configure } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import ReactGA from 'react-ga';

configure({ adapter: new Adapter() });

ReactGA.initialize('foo', { testMode: true });

window.matchMedia =
  window.matchMedia ||
  function() {
    return {
      matches: false,
      addListener: function() {},
      removeListener: function() {}
    };
  };

class LocalStorageMock {
  store = {};
  constructor() {
    this.store = {};
  }

  clear() {
    this.store = {};
  }

  getItem(key) {
    return this.store[key];
  }

  setItem(key, value) {
    this.store[key] = value.toString();
  }

  removeItem(key) {
    delete this.store[key];
  }
}

let localStorageMock =  new LocalStorageMock();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });
