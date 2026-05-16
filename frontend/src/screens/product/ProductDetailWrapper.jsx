import React from 'react';
import { useParams } from 'react-router-dom';
import SafeV2Wrapper from '../../components/SafeV2Wrapper';
import ProductDetailLegacy from './ProductDetailLegacy';
import ProductDetailV2 from './ProductDetailV2';

export default function ProductDetailWrapper(props) {
  const { id } = useParams();
  return <SafeV2Wrapper legacyComponent={ProductDetailLegacy} v2Component={ProductDetailV2} productId={id} screenName="product_detail" {...props} />;
}