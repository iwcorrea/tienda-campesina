import React from 'react';
import SafeV2Wrapper from '../../components/SafeV2Wrapper';
import TransportHomeLegacy from './TransportHomeLegacy'; // Ajusta la ruta si es necesario
import TransportHomeV2 from './TransportHomeV2';

export default function TransportHomeWrapper(props) {
  return (
    <SafeV2Wrapper
      legacyComponent={TransportHomeLegacy}
      v2Component={TransportHomeV2}
      {...props}
    />
  );
}