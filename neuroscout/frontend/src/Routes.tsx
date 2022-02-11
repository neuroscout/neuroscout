import * as React from 'react'
import { Route, Redirect, Switch } from 'react-router-dom'
import { message } from 'antd'

import './css/App.css'
import AnalysisList from './AnalysisList'
// import AnalysisBuilder from './analysis_builder/Builder';
const AnalysisBuilder = React.lazy(() => import('./analysis_builder/Builder'))
import { AppState } from './coretypes'
import { NotFound } from './HelperComponents'
import Home from './Home'
import { PredictorCollectionList } from './predictor_collection/CollectionList'
import EditProfile from './profile/EditProfile'
import PublicProfile from './profile/PublicProfile'
import UserList from './profile/UserList'
import PredictorRelatedDetailsView from './PredictorRelatedDetailsView'
import { DatasetDetailView } from './DatasetDetailView'

export default class Routes extends React.Component<
  AppState,
  Record<string, never>
> {
  render(): JSX.Element {
    return (
      <React.Suspense fallback={<div>Loading...</div>}>
        <Switch>
          <Route
            exact
            path="/"
            render={props => <Home {...this.props.user} />}
          />
          <Route
            exact
            path="/builder"
            render={props => {
              // This is a temporary solution to prevent non logged-in users from entering the builder.
              // Longer term to automatically redirect the user to the target URL after login we
              // need to implement something like the auth workflow example here:
              // https://reacttraining.com/react-router/web/example/auth-workflow
              if (this.props.user.loggedIn || this.props.user.openLogin) {
                return (
                  <AnalysisBuilder
                    updatedAnalysis={() => this.props.loadAnalyses()}
                    key={props.location.key}
                    datasets={this.props.datasets}
                    doTour={this.props.user.openTour}
                    userOwns
                    checkJWT={() => this.props.user.checkJWT(undefined)}
                  />
                )
              }
              void message.warning('Please log in first and try again')
              return <Redirect to="/" />
            }}
          />
          <Route
            path="/builder/:id"
            render={props => {
              return (
                <AnalysisBuilder
                  id={props.match.params.id}
                  updatedAnalysis={() => this.props.loadAnalyses()}
                  userOwns={
                    this.props.analyses === null
                      ? false
                      : this.props.analyses.filter(
                          x => x.id === props.match.params.id,
                        ).length > 0
                  }
                  datasets={this.props.datasets}
                  doTour={this.props.user.openTour}
                  checkJWT={() => this.props.user.checkJWT(undefined)}
                />
              )
            }}
          />
          <Route
            exact
            path="/public/:id"
            render={props => (
              <AnalysisBuilder
                id={props.match.params.id}
                updatedAnalysis={() => this.props.loadAnalyses()}
                userOwns={
                  this.props.analyses === null
                    ? false
                    : this.props.analyses.filter(
                        x => x.id === props.match.params.id,
                      ).length > 0
                }
                datasets={this.props.datasets}
                doTour={this.props.user.openTour}
                checkJWT={() => this.props.user.checkJWT(undefined)}
              />
            )}
          />
          <Route
            exact
            path="/public"
            key="public"
            render={props => (
              <AnalysisList
                analyses={this.props.publicAnalyses}
                cloneAnalysis={this.props.cloneAnalysis}
                datasets={this.props.datasets}
                publicList
                loggedIn={this.props.user.loggedIn}
                showOwner
              />
            )}
          />
          <Route
            exact
            path="/myanalyses"
            key="myanalyses"
            render={props => (
              <AnalysisList
                analyses={this.props.analyses}
                cloneAnalysis={this.props.cloneAnalysis}
                onDelete={this.props.onDelete}
                datasets={this.props.datasets}
                publicList={false}
                loggedIn={this.props.user.loggedIn}
              />
            )}
          />
          <Route
            path="/mycollections"
            render={props => (
              <PredictorCollectionList
                datasets={this.props.datasets}
                collections={this.props.user.predictorCollections}
                updateUser={this.props.user.update}
              />
            )}
          />
          <Route
            path="/profile/edit"
            render={props => <EditProfile {...this.props.user.profile} />}
          />
          <Route
            path="/profile/:user_name"
            render={props => {
              return (
                <PublicProfile
                  user_name={props.match.params.user_name}
                  datasets={this.props.datasets}
                  cloneAnalysis={this.props.cloneAnalysis}
                  loggedIn={this.props.user.loggedIn}
                  isUser={
                    props.match.params.user_name ===
                    '' + this.props.user.profile.user_name
                  }
                />
              )
            }}
          />
          <Route
            path="/profile"
            render={props => {
              if (this.props.user.profile.user_name !== '') {
                return (
                  <Redirect
                    to={'/profile/' + this.props.user.profile.user_name}
                  />
                )
              }
              return <Redirect to="/profiles" />
            }}
          />
          <Route
            path="/predictor/:id"
            render={props => {
              return <PredictorRelatedDetailsView id={props.match.params.id} />
            }}
          />
          <Route
            path="/dataset/:id"
            render={props => {
              const dataset = this.props.datasets.find(
                x => String(x.id) === String(props.match.params.id),
              )
              if (dataset) {
                return <DatasetDetailView {...dataset} />
              } else {
                return <NotFound />
              }
            }}
          />
          <Route component={NotFound} />
        </Switch>
      </React.Suspense>
    )
  }
}
