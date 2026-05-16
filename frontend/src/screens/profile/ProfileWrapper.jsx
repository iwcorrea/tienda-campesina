import React from 'react';
import SafeV2Wrapper from '../../components/SafeV2Wrapper';
import ProfileLegacy from './ProfileLegacy';
import ProfileV2 from './ProfileV2';

export default function ProfileWrapper(props) {
  return <SafeV2Wrapper legacyComponent={ProfileLegacy} v2Component={ProfileV2} screenName="profile" {...props} />;
}