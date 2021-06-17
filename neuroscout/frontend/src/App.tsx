/*
Top-level App component containing AppState. The App component is currently responsible for:
- Authentication (signup, login and logout)
- Routing
- Managing user's saved analyses (list display, clone and delete)
*/
import * as React from 'react'
import {
  BrowserRouter as Router,
  Route,
  Redirect,
  withRouter,
} from 'react-router-dom'
import { Layout, Modal, message } from 'antd'
import ReactGA from 'react-ga'
import memoize from 'memoize-one'

import './css/App.css'
import { api } from './api'
import { UserStore } from './user'
import { config } from './config'
import {
  ApiAnalysis,
  AppAnalysis,
  AppState,
  profileEditItems,
  ProfileState,
} from './coretypes'
import { LoginModal, ResetPasswordModal, SignupModal } from './Modals'
import Routes from './Routes'
import { jwtFetch, timeout } from './utils'
import { withTracker } from './utils/analytics'
import Navbar from './Navbar'
import Tour from './Tour'

const DOMAINROOT = config.server_url

const { Content } = Layout

if (config.ga_key) {
  ReactGA.initialize(config.ga_key)
}

type JWTChangeProps = {
  loadAnalyses: () => any
  checkAnalysesStatus: (key: number) => any
  jwt: string
  user_name: string
}

// This global var lets the dumb polling loops know when to exit.
let checkCount = 0

class JWTChange extends React.Component<JWTChangeProps, Record<string, never>> {
  jwtChanged = memoize((jwt, user_name) => {
    if (!!jwt && !!user_name) {
      this.props.loadAnalyses()
      checkCount += 1
      this.props.checkAnalysesStatus(checkCount)
    }
  })

  render() {
    this.jwtChanged(this.props.jwt, this.props.user_name)
    return null
  }
}

// Top-level App component
class App extends React.Component<Record<string, never>, AppState> {
  constructor(props) {
    super(props)

    this.state = {
      loadAnalyses: () => {
        void api.getMyAnalyses().then(analyses => {
          this.setState({ analyses })
        })
      },
      analyses: null,
      publicAnalyses: null,
      user: new UserStore(this.setState.bind(this)),
      datasets: [],
      onDelete: this.onDelete,
      cloneAnalysis: this.cloneAnalysis,
    }
  }

  componentDidMount() {
    void api.getPublicAnalyses().then(publicAnalyses => {
      this.setState({ publicAnalyses })
    })
    if (window.localStorage.getItem('jwt')) {
      void api
        .getUser()
        .then(response => {
          const updates = profileEditItems.reduce((acc, curr) => {
            acc[curr] = response[curr]
            return acc
          }, {})
          this.state.user.profile.update(updates, true)
        })
        .catch(error => {
          return
        })
    }
    void api.getDatasets(false).then(datasets => {
      if (datasets.length !== 0) {
        this.setState({ datasets })
      }
    })
  }

  /* short polling function checking api for inprocess analyses to see if
   * there have been any changes
   */
  checkAnalysesStatus = async (key: number) => {
    while (!(key < checkCount)) {
      if (!this.state.user.loggedIn) {
        return
      }
      let changeFlag = false
      if (this.state.analyses !== null) {
        const updatedAnalyses = this.state.analyses.map(async analysis => {
          if (['DRAFT', 'PASSED'].indexOf(analysis.status) > -1) {
            return analysis
          }
          const id = analysis.id
          return jwtFetch(`${DOMAINROOT}/api/analyses/${id}`, { method: 'get' })
            .then((data: ApiAnalysis) => {
              if (
                data.status !== analysis.status &&
                ['SUBMITTING', 'PENDING'].indexOf(data.status) === -1
              ) {
                changeFlag = true
                void message.info(
                  `analysis ${id} updated from ${analysis.status} to ${data.status}`,
                )
                analysis.status = data.status
              }
              return analysis
            })
            .catch(() => {
              return analysis
            })
        })
        void Promise.all(updatedAnalyses).then(values => {
          if (changeFlag) {
            this.setState({ analyses: values })
          }
        })
      }
      await timeout(120000)
    }
  }

  // Actually delete existing analysis given its hash ID, called from onDelete()
  deleteAnalysis = (id): void => {
    void api.deleteAnalysis(id).then(response => {
      if (response === true && this.state.analyses !== null) {
        this.setState({
          analyses: this.state.analyses.filter(a => a.id !== id),
        })
      }
    })
  }

  // Delete analysis if the necessary conditions are met
  onDelete = (analysis: AppAnalysis) => {
    const { deleteAnalysis } = this
    if (
      analysis.status &&
      ['DRAFT', 'FAILED'].includes(analysis.status) === false
    ) {
      void message.warning(
        'This analysis has already been submitted and cannot be deleted.',
      )
      return
    }
    Modal.confirm({
      title: 'Are you sure you want to delete this analysis?',
      content: '',
      okText: 'Yes',
      cancelText: 'No',
      onOk() {
        deleteAnalysis(analysis.id)
      },
    })
  }

  cloneAnalysis = (id: string): Promise<string> => {
    return api.cloneAnalysis(id).then(analysis => {
      if (analysis !== null) {
        if (this.state.analyses === null) {
          this.setState({ analyses: [analysis] })
        } else {
          this.setState({ analyses: this.state.analyses.concat([analysis]) })
        }
        return analysis.id
      }
      return ''
    })
  }

  AnalyticIndex = withTracker(Routes)

  render() {
    if (this.state.user.loggingOut) {
      return (
        <Router>
          <Redirect to="/" />
        </Router>
      )
    }

    return (
      <Router>
        <div>
          <JWTChange
            loadAnalyses={this.state.loadAnalyses}
            checkAnalysesStatus={this.checkAnalysesStatus}
            jwt={this.state.user.jwt}
            user_name={this.state.user.profile.user_name}
          />
          {this.state.user.openLogin && <LoginModal {...this.state.user} />}
          {this.state.user.openReset && (
            <ResetPasswordModal {...this.state.user} />
          )}
          {this.state.user.openSignup && <SignupModal {...this.state.user} />}
          {Tour(this.state.user.openTour, this.state.user.closeTour)}
          <Layout>
            <Content style={{ background: '#fff' }}>
              <Navbar {...this.state.user} />
              <br />
              <Route
                render={routeProps => (
                  <this.AnalyticIndex {...{ ...routeProps, ...this.state }} />
                )}
              />
            </Content>
          </Layout>
        </div>
      </Router>
    )
  }

  componentDidUpdate(prevProps, prevState) {
    // Need to do this so logout redirect only happens once, otherwise it'd be an infinite loop
    if (this.state.user.loggingOut) {
      this.state.user.update({ loggingOut: false })
      this.setState({ analyses: [] })
    }
  }
}

export default App
