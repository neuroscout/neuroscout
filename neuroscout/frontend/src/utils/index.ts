import { message } from 'antd';
import { authActions } from '../auth.actions';

// Display error to user as a UI notification and log it to console
export const displayError = (error: Error) => {
  try {
    message.error(error.toString(), 5);
  } catch (e) {
    // to make jsdom tests work
    return;
  } finally {
    // tslint:disable-next-line:no-console
    console.error(error);
  }
};

// moveItem moves an item in a given array up (toward index zero) or down (toward the last index),
// returning a new array
export type MoveItem<T> = (array: Array<T>, index: number, direction: 'up' | 'down') => Array<T>;
export const moveItem: MoveItem<any> = (array, index, direction) => {
  let newArray = [...array];
  if (direction === 'up') {
    if (index === 0) return newArray;
    newArray[index - 1] = array[index];
    newArray[index] = array[index - 1];
  } else if (direction === 'down') {
    if (index >= array.length - 1) return newArray;
    newArray[index + 1] = array[index];
    newArray[index] = array[index + 1];
  } else {
    throw new Error('Invalid direction');
  }
  return newArray;
};

async function pres(res) {
  // tslint:disable-next-line:no-console
  console.log(await res);
}

export const _fetch = (path: string, options?: object) => {
  return fetch(path, options).then(response => {
      // Need to figure this response out. openLogin triggers modal to popup,
      // but in next cycle. Keep track of request, and after submit on modal
      // run jwt fetch again?
      if (response.status === 401) {
        authActions.update({
          openLogin: true,
          loggedIn: false,
        });
        throw new Error('Please Login Again');
      }
      if (response.status >= 400) {
        pres(response);
        return { statusCode: response.status };
      } else {
        return response.json().then(json => {
          // Always add statusCode to the data object or array returned by response.json()
          // This is problematic if length is ever an attribute of a non array response from api.
          let copy: any;
          if ('length' in json) {
            // array
            copy = [...json];
            (copy as any).statusCode = response.status;
          } else {
            // object
            copy = { ...json, statusCode: response.status };
          }
          return copy;
        });
      }
    });
};

// Wrapper around the standard 'fetch' that takes care of:
// - Adding jwt to request header
// - Decoding JSON response and adding the response status code to decoded JSON object
export const jwtFetch = (path: string, options?: any, noCT?: boolean) => {
  const jwt = window.localStorage.getItem('jwt');

  if (!options) { options = {}; }
  if (!options.headers) { options.headers = {}; }

  options.headers.Authorization = 'JWT ' + jwt;

  if (!options.headers['Content-type'] && !noCT) {
    options.headers['Content-type'] = 'application/json';
  }

  return _fetch(path, options);
};

export const timeout = (ms: number) => {
      return new Promise(resolve => setTimeout(resolve, ms));
};

export const alphaSort = (x: string[]) => {
  return x.sort((a, b) => a.localeCompare(b));
};

export const reorder = (list: any[], startIndex: number, endIndex: number): any[] => {
  const result = [...list];
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);

  return result;
};

export const isDefined = <T>(argument: T | undefined): argument is T => {
    return argument !== undefined;
};

// Number column can be a mixture of ints and strings sometimes, hence the cast to string
// number is stored as text in postgres, should see about treating it consistently in app
const _sortRuns = (keys, a, b) => {
  for (var i = 0; i < keys.length; i++) {
    let _a = String(a[keys[i]]);
    let _b = String(b[keys[i]]);
    let cmp = _a.localeCompare(_b, undefined, {numeric: true});
    if (cmp !== 0) { return cmp; }
  }
  return 0;
};

// Comparison functions to pass to sort for arrays of type Run by differnt keys
export const sortSub = _sortRuns.bind(null, ['subject', 'number', 'session']);
export const sortNum = _sortRuns.bind(null, ['number', 'subject',  'session']);
export const sortSes = _sortRuns.bind(null, ['session', 'subject', 'number']);
