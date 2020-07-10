/*
Top-level App component containing AppState. The App component is currently responsible for:
- Authentication (signup, login and logout)
- Routing
- Managing user's saved analyses (list display, clone and delete)
*/
import * as React from 'react';
import { BrowserRouter as Router, Route, Redirect } from 'react-router-dom';
import { Layout, Modal, message } from 'antd';
import ReactGA from 'react-ga';
import memoize from 'memoize-one';

import './css/App.css';
import { api } from './api';
import { UserStore } from './user';
import { config } from './config';
import { ApiAnalysis, AppAnalysis, AppState, profileEditItems, ProfileState } from './coretypes';
import { LoginModal, ResetPasswordModal, SignupModal } from './Modals';
import Routes from './Routes';
import { jwtFetch, timeout } from './utils';
import { withTracker } from './utils/analytics';
import Navbar from './Navbar';
import Tour from './Tour';

const DOMAINROOT = config.server_url;

const { Content } = Layout;

if (config.ga_key) {
  ReactGA.initialize(config.ga_key);
}

type JWTChangeProps = {
  loadAnalyses:  () => any;
  checkAnalysesStatus: (key: number) => any;
  jwt: string;
};

// This global var lets the dumb polling loops know when to exit.
let checkCount = 0;

class JWTChange extends React.Component<JWTChangeProps, {}> {
  constructor(props) {
    super(props);
    if (this.props.jwt !== '' && this.props.jwt !== null) {
      props.loadAnalyses();
      checkCount += 1;
      props.checkAnalysesStatus(checkCount);
    }
  }

  componentDidUpdate(prevProps, prevState) {
    if (!!this.props.jwt && this.props.jwt !== prevProps.jwt) {
      this.props.loadAnalyses();
    }
  }

  render() { return null; }
}

// Top-level App component
class App extends React.Component<{}, AppState> {
  constructor(props) {
    super(props);
    
    this.state = {
      loadAnalyses: () => {
        api.getAnalyses().then(analyses => {
          this.setState({ analyses });
        });
      },
      analyses: null,
      publicAnalyses: null,
      user: new UserStore(this.setState.bind(this)),
      datasets: [],
      onDelete: this.onDelete,
      cloneAnalysis: this.cloneAnalysis,
    };
    api.getPublicAnalyses().then((publicAnalyses) => {
      this.setState({ publicAnalyses });
    });
    api.getUser().then((response) => {
      if (response.statusCode !== 200) {
        return;
      }
      let updates = profileEditItems.reduce((acc, curr) => {acc[curr] = response[curr]; return acc; }, {});
      this.state.user.profile.update(updates, true);
    });
    api.getDatasets(false).then((datasets) => {
      if (datasets.length !== 0) {
        this.setState({ datasets });
      }
    });
  }

  /* short polling function checking api for inprocess analyses to see if
   * there have been any changes
   */
  checkAnalysesStatus = async (key: number) => {
    while (true) {
      if (key < checkCount) { return; }
      if (!(this.state.user.loggedIn)) { return; }
      let changeFlag = false;
      if (this.state.analyses !== null) {
        let updatedAnalyses = this.state.analyses.map(async (analysis) => {
          if (['DRAFT', 'PASSED'].indexOf(analysis.status) > -1) {
            return analysis;
          }
          let id = analysis.id;
          return jwtFetch(`${DOMAINROOT}/api/analyses/${id}`, { method: 'get' })
            .then((data: ApiAnalysis) => {
              if ((data.status !== analysis.status)
                  && (['SUBMITTING', 'PENDING'].indexOf(data.status) === -1)) {
                changeFlag = true;
                message.info(`analysis ${id} updated from ${analysis.status} to ${data.status}`);
                analysis.status = data.status;
              }
              return analysis;
          })
          .catch(() => { return analysis; });
        });
        Promise.all(updatedAnalyses).then((values) => {
          if (changeFlag) {
            this.setState({ analyses: values});
          }
        });
      }
      await timeout(12000);
    }
  };

  // Actually delete existing analysis given its hash ID, called from onDelete()
  deleteAnalysis = (id): void => {
    api.deleteAnalysis(id).then((response) => {
      if (response === true && this.state.analyses !== null) {
        this.setState({ analyses: this.state.analyses.filter(a => a.id !== id) });
      }
    });
  }

  // Delete analysis if the necessary conditions are met
  onDelete = (analysis: AppAnalysis) => {
    const { deleteAnalysis } = this;
    if (analysis.status && ['DRAFT', 'FAILED'].includes(analysis.status) === false) {
      message.warning('This analysis has already been submitted and cannot be deleted.');
      return;
    }
    Modal.confirm({
      title: 'Are you sure you want to delete this analysis?',
      content: '',
      okText: 'Yes',
      cancelText: 'No',
      onOk() {
        deleteAnalysis(analysis.id);
      }
      });
  }

  cloneAnalysis = (id: string): void => {
    api.cloneAnalysis(id).then((analysis) => {
      if (analysis !== null) {
        if (this.state.analyses === null) {
          this.setState({ analyses: [analysis] });
        } else {
          this.setState({ analyses: this.state.analyses.concat([analysis]) });
        }
      }
    });
  };

  AnalyticIndex = withTracker(Routes);

  render() {
    if (this.state.user.loggingOut) {
      return (
        <Router>
          <Redirect to="/" />
        </Router>
      );
    }

    return (
      <Router>
        <div>
          <JWTChange
            loadAnalyses={this.state.loadAnalyses}
            checkAnalysesStatus={this.checkAnalysesStatus}
            jwt={this.state.user.jwt}
          />
          {this.state.user.openLogin && <LoginModal {...this.state.user} />}
          {this.state.user.openReset && <ResetPasswordModal {...this.state.user} />}
          {this.state.user.openSignup && <SignupModal {...this.state.user} />}
          <Tour
            isOpen={this.state.user.openTour}
            closeTour={this.state.user.closeTour}
          />
          <Layout>
            <Content style={{ background: '#fff' }}>
              <Navbar {...this.state.user} />
              <br />
              <Route 
                render={(routeProps) => 
                  <this.AnalyticIndex {...{...routeProps, ...this.state}} />
                }
              />
            </Content>
          </Layout>
        </div>
      </Router>
    );
  }

  componentDidUpdate(prevProps, prevState) {
    // Need to do this so logout redirect only happens once, otherwise it'd be an infinite loop
    if (this.state.user.loggingOut) {
      this.state.user.update({ loggingOut: false });
      this.setState({analyses: []});
    }
  }
}

export default App;
