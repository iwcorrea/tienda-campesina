import React from 'react';
import SafeV2Wrapper from '../../components/SafeV2Wrapper';
import PedidoDetailLegacy from './PedidoDetailLegacy';
import TimelineV2 from './TimelineV2';

export default function PedidoDetailWrapper({ match, ...rest }) {
  const orderId = match.params.id;
  return (
    <SafeV2Wrapper
      legacyComponent={PedidoDetailLegacy}
      v2Component={TimelineV2}
      orderId={orderId}
      {...rest}
    />
  );
}