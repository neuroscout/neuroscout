import * as React from 'react';
import { Button, Card, Icon, Dropdown, Skeleton } from 'antd';
import { config } from './config';
import { displayError, jwtFetch, alphaSort, timeout } from './utils';

const domainRoot = config.server_url;
const ButtonGroup = Button.Group;

type bibProps = {
  analysisId?: string,
};

interface BibState {
  tools: any[];
  data: any[];
  extractors: any[];

  bibLoaded: boolean;
}

class RefList extends React.Component<{refs: any[]}, {}> {
  render() {
    let items = this.props.refs.map((item, key) =>
      <li key={key}>{item.title}</li>
    );

    return(
    <div>
      <ul>
      {items}
      </ul>
    </div>
    );
  }
}

export class BibliographyTab extends React.Component<bibProps, BibState> {
  constructor(props) {
    super(props);
    let state: BibState = {
      tools: [],
      data: [],
      extractors: [],
      bibLoaded: false,
    };
    this.state = state;
  }

  loadBib = (): void => {
    let id = this.props.analysisId;
    let url = `${domainRoot}/api/analyses/${id}/bibliography`;
    let state = {...this.state};
    jwtFetch(url, { method: 'GET' })
    .then((res) => {
      state.tools = res.tools;
      state.data = res.data;
      state.extractors = res.extractors;

      state.bibLoaded = true;
      this.setState({...state});
    });
  };

  componentDidMount() {
    if (this.state.bibLoaded === false) {
      this.loadBib();
    }
  }

  render() {

    return(
      <div>
          <p>
            Below are the references for the tools, data, and extractors used in this analysis.
            Be sure to cite these references if you publish any results stemming from this analysis.
          </p>
          <Card title="Scientific Software">
          <Skeleton loading={this.state.bibLoaded === false}>
            <RefList refs={this.state.tools}/>
          </Skeleton>
          </Card>
          <br/>
          <Card title="Datasets">
          <Skeleton loading={this.state.bibLoaded === false}>
            <RefList refs={this.state.data}/>
          </Skeleton>
          </Card>
          <br/>
          <Card title="Feature Extractors">
          <Skeleton loading={this.state.bibLoaded === false}>
            <RefList refs={this.state.extractors}/>
          </Skeleton>

          </Card>
          <br/>

          <Card title="Export All" bordered={false} style={{ width: 400 }}>
          <ButtonGroup>
            <Button icon="download">BibTex</Button>
            <Button icon="download">CSL-JSON</Button>
            <Button icon="download">Text - APA</Button>
          </ButtonGroup>
          </Card>
      </div>
    );
  }
}
