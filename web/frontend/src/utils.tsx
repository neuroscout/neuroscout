import { message } from 'antd';
export const displayError = (error: Error) => message.error(error.toString());
