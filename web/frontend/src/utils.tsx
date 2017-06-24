import * as React from 'react';
import { message } from 'antd';
export const displayError = (error: Error) => message.error(error.toString());

export const jwtFetch = (path: string, options?: object) => {
  const jwt = window.localStorage.getItem('jwt');
  if (jwt === null) {
    const error = 'JWT not found in local storage. You must be logged in.';
    message.error(error);
    throw error;
  }
  const newOptions = {
    ...options,
    headers: {
      'Content-type': 'application/json',
      'Authorization': 'JWT ' + jwt
    }
  };
  return fetch(path, newOptions);
};

export const Space = (props: {}) => <span>{' '}</span>;