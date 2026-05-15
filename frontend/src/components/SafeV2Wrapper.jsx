import React, { useContext } from 'react';
import { isV2EnabledForUser } from '../config/features';
import { track } from '../telemetry/pilot';
import { AuthContext } from '../context/AuthContext'; // Ajusta la ruta según tu proyecto

class SafeV2Wrapper extends React.Component {
  static contextType = AuthContext;
  
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
    const user = this.context?.user || null;
    const enabled = isV2EnabledForUser(user);
    const { legacyComponent: Legacy, v2Component: V2, screenName, ...rest } = this.props;

    if (this.state.hasError || !enabled) {
      return <Legacy {...rest} />;
    }

    return <V2 {...rest} />;
  }
}

export default SafeV2Wrapper;