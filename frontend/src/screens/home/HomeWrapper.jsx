import React from 'react';
import SafeV2Wrapper from '../../components/SafeV2Wrapper';
import HomeLegacy from './HomeLegacy';
import HomeV2 from './HomeV2';

export default function HomeWrapper(props) {
  return <SafeV2Wrapper legacyComponent={HomeLegacy} v2Component={HomeV2} screenName="home" {...props} />;
}