import { Duration, Stack, StackProps, CfnOutput } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from "aws-cdk-lib/aws-s3"
import * as lambda from "aws-cdk-lib/aws-lambda"
import * as fs from "fs";
import * as cdk from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam"
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as tasks from "aws-cdk-lib/aws-stepfunctions-tasks";
import * as s3n from "aws-cdk-lib/aws-s3-notifications";

export class VoithruStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);
    const contentsBucket = new s3.Bucket(this, "contentsBucket");
    const resultBucket = new s3.Bucket(this, "resultBucket");

    const haikuLambda = new lambda.Function(this, "haikuLambdaFunction", {
      code: new lambda.InlineCode(
        fs.readFileSync("lambda/haikuLambda.py", { encoding: "utf-8" })
      ),
      handler: "index.lambda_handler",
      timeout: cdk.Duration.seconds(300),
      environment: {
       
      },
      runtime: lambda.Runtime.PYTHON_3_12,
    });
    const sonnetLambda = new lambda.Function(this, "sonnetLambdaFunction", {
      code: new lambda.InlineCode(
        fs.readFileSync("lambda/sonnetLambda.py", { encoding: "utf-8" })
      ),
      handler: "index.lambda_handler",
      timeout: cdk.Duration.seconds(300),
      environment: {
        RESULT_BUCKET: resultBucket.bucketName
      },
      runtime: lambda.Runtime.PYTHON_3_12,
    });

    haikuLambda.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:*"],
        resources: ["*"],
      })
    );
    
    haikuLambda.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["s3:*"],
        resources: ["*"],
      })
    );
    
    sonnetLambda.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:*"],
        resources: ["*"],
      })
    );
    sonnetLambda.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["s3:*"],
        resources: ["*"],
      })
    );

    const haiku = new tasks.LambdaInvoke(this, "haikuLambda", {
      lambdaFunction: haikuLambda,
      outputPath: "$.Payload"
    })

    const sonnet = new tasks.LambdaInvoke(this, "sonnetLambda", {
      lambdaFunction: sonnetLambda,
      outputPath: "$.Payload"
    })

    const successState = new sfn.Pass(this, "SuccessState");
    const definition = haiku.next(sonnet);

    const stateMachine = new sfn.StateMachine(this, "stateMachine", {
      definition,
      timeout: cdk.Duration.minutes(15)
    });

    const startLambda = new lambda.Function(this, "startLambdaFunction", {
      code: new lambda.InlineCode(
        fs.readFileSync("lambda/startLambda.py", { encoding: "utf-8" })
      ),
      handler: "index.lambda_handler",
      timeout: cdk.Duration.seconds(300),
      environment: {
        STATE_MACHINE_ARN : stateMachine.stateMachineArn
      },
      runtime: lambda.Runtime.PYTHON_3_12,
    });

    stateMachine.grantStartExecution(startLambda);
    contentsBucket.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.LambdaDestination(startLambda));
    contentsBucket.grantRead(startLambda);
    contentsBucket.grantRead(haikuLambda);
    contentsBucket.grantRead(sonnetLambda);
    resultBucket.grantPut(sonnetLambda);
    resultBucket.grantWrite(sonnetLambda);
    haikuLambda.grantInvoke(stateMachine.role);
    sonnetLambda.grantInvoke(stateMachine.role);

    new CfnOutput(this, "STATEMACHINE", {
      value: stateMachine.stateMachineArn,
    });
    new CfnOutput(this, "CONTENTSBUCKET", {
      value: contentsBucket.bucketName,
    });
    new CfnOutput(this, "RESULTBUCKET", {
      value: resultBucket.bucketName,
    });
  }
}
