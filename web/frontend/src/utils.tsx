import * as React from 'react';
import { message } from 'antd';

export const displayError = (error: Error) => {
  try {
    message.error(error.toString(), 5);
  } catch (e) { // to make jsdom tests work
    return;
  } finally{
    console.error(error);
  }
};

export const jwtFetch = (path: string, options?: object) => {
  const jwt = window.localStorage.getItem('jwt');
  if (jwt === null) {
    const error = 'JWT not found in local storage. You must be logged in.';
    message.error(error);
  }
  const newOptions = {
    ...options,
    headers: {
      'Content-type': 'application/json',
      'Authorization': 'JWT ' + jwt
    }
  };
  return fetch(path, newOptions)
    .then(response => {
      if (response.status !== 200) displayError(new Error(`HTTP ${response.status} on ${path}`));
      return response.json().then(json => {
        // Always add statusCode to the data object or array returned by response.json()
        let copy: any;
        if ('length' in json) { // array
          copy = [...json];
          (copy as any).statusCode = response.status;
        } else { // object
          copy = { ...json, statusCode: response.status }
        }
        return copy;
      }
      );
    });

};

export const Space = (props: {}) => <span>{' '}</span>;