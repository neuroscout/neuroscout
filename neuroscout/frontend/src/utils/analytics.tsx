import * as React from 'react'
import GoogleAnalytics from 'react-ga'
import { RouteComponentProps } from 'react-router-dom'

GoogleAnalytics.initialize('UA-143429930-1')

export function withTracker(WrappedComponent, options = {}) {
  const trackPage = (page: string): void => {
    GoogleAnalytics.set({
      page,
      ...options,
    })
    GoogleAnalytics.pageview(page)
  }

  const HOC = class extends React.Component<RouteComponentProps> {
    displayName = 'GAHOCWrapper'
    componentDidMount() {
      const page = this.props.location.pathname + this.props.location.search
      trackPage(page)
    }

    componentDidUpdate(prevProps: RouteComponentProps) {
      const currentPage =
        prevProps.location.pathname + prevProps.location.search
      const nextPage = this.props.location.pathname + this.props.location.search

      if (currentPage !== nextPage) {
        trackPage(nextPage)
      }
    }

    render() {
      return <WrappedComponent {...this.props} />
    }
  }

  return HOC
}
