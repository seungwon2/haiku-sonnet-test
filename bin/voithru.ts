#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { VoithruStack } from '../lib/voithru-stack';

const app = new cdk.App();
new VoithruStack(app, 'VoithruStack');
