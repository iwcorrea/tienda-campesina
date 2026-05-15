import React from 'react';
import { useParams } from 'react-router-dom';
import SafeV2Wrapper from '../../components/SafeV2Wrapper';
import PedidoDetailLegacy from './PedidoDetailLegacy';
import TimelineV2 from './TimelineV2';

export default function PedidoDetailWrapper(props) {
  const { id } = useParams();
  return (
    <SafeV2Wrapper
      legacyComponent={PedidoDetailLegacy}
      v2Component={TimelineV2}
      orderId={id}
      {...props}
    />
  );
}