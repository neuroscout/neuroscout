import * as React from 'react';
import { Tag, Icon } from 'antd';

// Status component to display the color-coded analysis status with a locked/unlocked icon
const Status = (props: { status: string }) => {
  const { status } = props;
  const color: string = {
    DRAFT: 'blue',
    PENDING: 'orange',
    COMPILED: 'green'
  }[status];
  return (
    <span>
      <Tag color={color}>
        {status === 'DRAFT' ? <Icon type="unlock" /> : <Icon type="lock" />}
        {' ' + status}
      </Tag>
    </span>
  );
};

export default Status;
