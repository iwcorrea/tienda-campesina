import React from 'react';
import SafeV2Wrapper from '../../components/SafeV2Wrapper';
import DraftOrdersLegacy from './DraftOrdersLegacy'; // placeholder
import DraftOrdersV2 from './DraftOrdersV2';

export default function DraftOrdersWrapper(props) {
  return <SafeV2Wrapper legacyComponent={DraftOrdersLegacy} v2Component={DraftOrdersV2} screenName="draft_orders" {...props} />;
}