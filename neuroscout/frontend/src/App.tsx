/*
Top-level App component containing AppState. The App component is currently responsible for:
- Authentication (signup, login and logout)
- Routing
- Managing user's saved analyses (list display, clone and delete)
*/
import * as React from 'react';
import { BrowserRouter as Router, Route, Redirect } from 'react-router-dom';
import Reflux from 'reflux';
import { Layout, Modal, message } from 'antd';
import ReactGA from 'react-ga';

import './css/App.css';
import { api } from './api';
import { AuthStore } from './auth.store';
import { authActions } from './auth.actions';
import { config } from './config';
import { ApiAnalysis, AppAnalysis, AppState } from './coretypes';
import { LoginModal, ResetPasswordModal, SignupModal } from './Modals';
import Routes from './Routes';
import { jwtFetch, timeout } from './utils';
import { withTracker } from './utils/analytics';
import Navbar from './Navbar';
import Tour from './Tour';

const DOMAINROOT = config.server_url;

const { Content } = Layout;

ReactGA.initialize(config.ga_key);

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
    if (this.props.jwt !== '') {
      props.loadAnalyses();
      checkCount += 1;
      props.checkAnalysesStatus(checkCount);
    }
  }

  render() { return null; }
}

// Top-level App component
class App extends Reflux.Component<any, {}, AppState> {
  constructor(props) {
    super(props);
    this.state = {
      loadAnalyses: () => {
        api.getAnalyses().then(analyses => {
          this.setState({ analyses });
        });
      },
      analyses: [],
      publicAnalyses: [],
      auth: authActions.getInitialState(),
      datasets: [],
      onDelete: this.onDelete,
      cloneAnalysis: this.cloneAnalysis
    };
    this.store = AuthStore;
    api.getPublicAnalyses().then((publicAnalyses) => {
      this.setState({ publicAnalyses });
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
      if (!(this.state.auth.loggedIn)) { return; }
      let changeFlag = false;
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
      await timeout(10000000);
    }
  };

  // Actually delete existing analysis given its hash ID, called from onDelete()
  deleteAnalysis = (id): void => {
    api.deleteAnalysis(id).then((response) => {
      if (response === true) {
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
        this.setState({ analyses: this.state.analyses.concat([analysis]) });
      }
    });
  };

  AnalyticIndex = withTracker(Routes);

  render() {
    if (this.state.auth.loggingOut) {
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
            jwt={this.state.auth.jwt}
          />
          {this.state.auth.openLogin && <LoginModal {...this.state.auth} />}
          {this.state.auth.openReset && <ResetPasswordModal {...this.state.auth} />}
          {this.state.auth.openSignup && <SignupModal {...this.state.auth} />}
          <Tour
            isOpen={this.state.auth.openTour}
            closeTour={authActions.closeTour}
          />
          <Layout>
            <Content style={{ background: '#fff' }}>
              <Navbar {...this.state.auth} />
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
    if (this.state.auth.loggingOut) authActions.update({ loggingOut: false });
  }
}

export default App;
