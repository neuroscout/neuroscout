import { message } from 'antd'
import { Predictor } from '../coretypes'
// Display error to user as a UI notification and log it to console
export const displayError = (error: Error): void => {
  try {
    void message.error(error.toString(), 5)
  } catch (e) {
    // to make jsdom tests work
    return
  } finally {
    // eslint-disable-next-line no-console
    console.error(error)
  }
}

// moveItem moves an item in a given array up (toward index zero) or down (toward the last index),
// returning a new array
export type MoveItem<T> = (
  array: Array<T>,
  index: number,
  direction: 'up' | 'down',
) => Array<T>
export const moveItem = <T>(
  array: Array<T>,
  index: number,
  direction: 'up' | 'down',
): Array<T> => {
  const newArray: Array<T> = [...array]
  if (direction === 'up') {
    if (index === 0) return newArray
    newArray[index - 1] = array[index]
    newArray[index] = array[index - 1]
  } else if (direction === 'down') {
    if (index >= array.length - 1) return newArray
    newArray[index + 1] = array[index]
    newArray[index] = array[index + 1]
  } else {
    throw new Error('Invalid direction')
  }
  return newArray
}

async function pres(res) {
  // eslint-disable-next-line no-console
  console.log(await res)
}

export const _fetch = (path: string, options?: Record<string, unknown>) => {
  return fetch(path, options).then(response => {
    if (response.status === 401) {
      throw new Error('Please Login Again')
    }
    if (response.status !== 200 && response.status !== 422) {
      // pres(response);
      return { statusCode: response.status }
    } else {
      return response.json().then(json => {
        // Always add statusCode to the data object or array returned by response.json()
        // This is problematic if length is ever an attribute of a non array response from api.
        let copy: any
        if ('length' in json) {
          // array
          copy = [...json]
          copy.statusCode = response.status
        } else {
          // object
          copy = { ...json, statusCode: response.status }
        }
        return copy
      })
    }
  })
}

// Wrapper around the standard 'fetch' that takes care of:
// - Adding jwt to request header
// - Decoding JSON response and adding the response status code to decoded JSON object
export const jwtFetch = (path: string, options?: any, noCT?: boolean) => {
  const jwt = window.localStorage.getItem('jwt')
  if (!jwt) {
    return _fetch(path, options)
  }

  if (!options) {
    options = {}
  }
  if (!options.headers) {
    options.headers = {}
  }

  options.headers.Authorization = 'JWT ' + jwt

  if (!options.headers['Content-type'] && !noCT) {
    options.headers['Content-type'] = 'application/json'
  }

  return _fetch(path, options)
}

export const timeout = (ms: number) => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export const alphaSort = (x: string[]) => {
  return x.sort((a, b) => a.localeCompare(b))
}

export const reorder = (
  list: any[],
  startIndex: number,
  endIndex: number,
): any[] => {
  const result = [...list]
  const [removed] = result.splice(startIndex, 1)
  result.splice(endIndex, 0, removed)

  return result
}

export const isDefined = <T>(argument: T | undefined): argument is T => {
  return argument !== undefined
}

// Number column can be a mixture of ints and strings sometimes, hence the cast to string
// number is stored as text in postgres, should see about treating it consistently in app
const _sortRuns = (keys, a, b) => {
  for (let i = 0; i < keys.length; i++) {
    const _a = String(a[keys[i]])
    const _b = String(b[keys[i]])
    const cmp = _a.localeCompare(_b, undefined, { numeric: true })
    if (cmp !== 0) {
      return cmp
    }
  }
  return 0
}

// Comparison functions to pass to sort for arrays of type Run by differnt keys
export const sortSub = _sortRuns.bind(null, ['subject', 'number', 'session'])
export const sortNum = _sortRuns.bind(null, ['number', 'subject', 'session'])
export const sortSes = _sortRuns.bind(null, ['session', 'subject', 'number'])

export const formatDbTime = (inTime: string): string => {
  const date = inTime.split('-')
  return `${date[2].slice(0, 2)}-${date[1]}-${date[0].slice(2, 4)}`
}

export const predictorColor = (predictor: Predictor): string => {
  const lookup = {
    '': '#f5222d',
    text: '#cc7ee0',
    video: '#fa8c16',
    audio: '#faad14',
    image: '#a0d911',
  }
  if (
    predictor &&
    predictor.extracted_feature &&
    predictor.extracted_feature.modality
  ) {
    return lookup[predictor.extracted_feature.modality]
  } else if (predictor.source === 'fmriprep') {
    return '#858d99'
  } else {
    return '#474747'
  }
}
