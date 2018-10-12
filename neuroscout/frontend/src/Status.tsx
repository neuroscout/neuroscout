import * as React from 'react';
import { Tag, Icon } from 'antd';
import { config } from './config';

const domainRoot = config.server_url;

export class Status extends React.Component<{status?: string, analysisId?: string}, {}> {

    render() {
      let { analysisId, status } = this.props;
      if (status === undefined) {
        status = 'DRAFT';
      }
      const color: string = {
        DRAFT: 'blue',
        PENDING: 'orange',
        FAILED: 'red',
        PASSED: 'green'
      }[status];

      let bundleLink;
      if (status === 'PASSED' && analysisId) {
        bundleLink = `${domainRoot}/analyses/${analysisId}_bundle.tar.gz`;
      }

      return(
        <span>
          <Tag color={color}>
            {status === 'DRAFT' ? <Icon type="unlock" /> : <Icon type="lock" />}
            {' ' + status}
          </Tag>
        </span>
      );
    }
}

export class DLLink extends React.Component<{status?: string, analysisId?: string}, {}> {
    render() {
      let { analysisId, status } = this.props;
      if (status === undefined) {
        status = 'DRAFT';
      }

      let bundleLink;
      if (status === 'PASSED' && analysisId) {
        bundleLink = `${domainRoot}/analyses/${analysisId}_bundle.tar.gz`;
      }

      return(
          <span>
            <a href={bundleLink}>Download</a>
          </span>
      );
    }
}
