import React from 'react';
import { FEATURE_V2_PANTALLAS } from '../config/features';

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
  }

  render() {
    const { legacyComponent: Legacy, v2Component: V2, ...rest } = this.props;

    if (this.state.hasError || !FEATURE_V2_PANTALLAS) {
      return <Legacy {...rest} />;
    }

    return <V2 {...rest} />;
  }
}

export default SafeV2Wrapper;