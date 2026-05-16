import React from 'react';
import SafeV2Wrapper from '../../components/SafeV2Wrapper';
import CatalogLegacy from './CatalogLegacy';  // placeholder o el antiguo
import CatalogV2 from './CatalogV2';

export default function CatalogWrapper(props) {
  return <SafeV2Wrapper legacyComponent={CatalogLegacy} v2Component={CatalogV2} screenName="catalog" {...props} />;
}