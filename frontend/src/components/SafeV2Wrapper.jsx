import React from 'react';
import { FEATURE_V2_PANTALLAS } from '../config/features';
import { track } from '../telemetry/pilot';

class SafeV2Wrapper extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('[SafeV2Wrapper] Error en V2, usando legacy:', error, info);
    const screenName = this.props.screenName || 'unknown';
    track('error_boundary_triggered', { screen: screenName, error_message: error.message });
  }

  render() {
    const enabled = FEATURE_V2_PANTALLAS;
    const { legacyComponent: Legacy, v2Component: V2, ...rest } = this.props;

    if (this.state.hasError || !enabled) {
      return <Legacy {...rest} />;
    }

    return <V2 {...rest} />;
  }
}

export default SafeV2Wrapper;