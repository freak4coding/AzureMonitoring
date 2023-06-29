# importing all the necessary libraries
# import datetime
# from azure.identity import ClientSecretCredential
from azure.identity import InteractiveBrowserCredential
# from azure.identity import AzureCliCredential
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
import Server
# import re
import sys
import threading
import csv

# f = open("FinalOutput.csv","w")
# sys.stdout = f
credential = InteractiveBrowserCredential()

class RunHistory:
    def __init__(self, list, flag, last_updated_after, last_updated_before):
        self.list = list
        self.last_updated_after = last_updated_after
        self.last_updated_before = last_updated_before
        self.flag = flag

    def timeConversion(TimeInSec):
        if TimeInSec < 60:
            return str(TimeInSec) + " Sec"
        elif TimeInSec < 3600:
            return str(round(TimeInSec / 60,2)) + " Min"
        else:
            return str(round(TimeInSec / 3600,2)) + " Hrs"
    
    def printFailureMessage(RunMsz):
        if RunMsz == "":
            return "No Error"
        else:
            return RunMsz

    def format_LTA_LTB(time):
        # print(time+":00.0000000Z")
        return time+":00.0000000Z"

    def get_master_pipeline_adf(subscription_id, resource_group_name, data_factory_name, pipelineNameList,last_updated_after,last_updated_before):
        client = DataFactoryManagementClient(credential=credential,subscription_id=subscription_id)
        CompleteData = []

        for pipelineName in pipelineNameList:
            try:
                pipeline_runs = client.pipeline_runs.query_by_factory(
                        resource_group_name=resource_group_name,
                        factory_name=data_factory_name,
                        filter_parameters={
                            "filters": [{"operand": "PipelineName", "operator": "Equals", "values": [pipelineName]}],
                            "lastUpdatedAfter": RunHistory.format_LTA_LTB(last_updated_after),
                            "lastUpdatedBefore": RunHistory.format_LTA_LTB(last_updated_before),
                        },
                    )
                for run in pipeline_runs.value:
                    if run is not None:
                        CompleteData.append({"ADF":data_factory_name,"RunId":run.run_id,"PipelineName":run.pipeline_name,"Status":run.status,"RunStartDate":run.run_start,"RunEndDate":run.run_end,"Duration":run.duration_in_ms/1000,"ErrorMessage":RunHistory.printFailureMessage(run.message)})                
            except Exception as e:
                print(e)
        return(CompleteData)

    def get_activity_list(subscription_id, resource_group_name, data_factory_name, pipeline_run_id,LastUpdateAfter,LastUpdateBefore):
        # ActivityResponse = [{"PipelineRunId":pipeline_run_id}]
        ActivityResponse = []
        if pipeline_run_id != "":    
            adf_client =  DataFactoryManagementClient(credential, subscription_id)
                # pipeline_run = adf_client.pipeline_runs.get(resource_group_name, data_factory_name, pipeline_run_id)
            try:                      
                filter_params = RunFilterParameters(last_updated_after = RunHistory.format_LTA_LTB(LastUpdateAfter),
                            last_updated_before = RunHistory.format_LTA_LTB(LastUpdateBefore))                            
                query_response = adf_client.activity_runs.query_by_pipeline_run(resource_group_name,data_factory_name,pipeline_run_id,filter_params)    
                for out in query_response.value:
                    if out.activity_type == "ExecutePipeline":
                                        # print("{},{},{},{},{},{},{}".format(out.activity_type,out.activity_name,out.status,out.run_start,out.run_end,out.duration_in_ms))
                                        # ActivityResponse.append({"ActivityName":out.input["pipeline"]["referenceName"],"Status":out.status,"Duration":RunHistory.timeConversion(out.duration_in_ms/1000),"ErrorMesssage":run.message})
                        ActivityResponse.append({"ActivityRunId":out.activity_run_id,"Type":"Execute Activity","ActivityName":out.input["pipeline"]["referenceName"],"Status":out.status,"RunStartDate":out.activity_run_start,"RunEndDate":out.activity_run_end,"Duration":out.duration_in_ms/1000,"ErrorMessage":RunHistory.printFailureMessage(out.error["message"])})
                    else:
                        ActivityResponse.append({"ActivityRunId":out.activity_run_id,"Type":"Activity","ActivityName":out.activity_name,"Status":out.status,"RunStartDate":out.activity_run_start,"RunEndDate":out.activity_run_end,"Duration":out.duration_in_ms/1000,"ErrorMessage":RunHistory.printFailureMessage(out.error["message"])})
                        #     # # print(ActivityResponse)
                        #     # print(ActivityResponse)                      
            except Exception as e:
                print(e)
                        # # run["ActivityResponse"] = ActivityResponse  
        else:
            print("")
        return ActivityResponse

class SubscriptionDetail:

    def getListOfPipelines(resourceGroupName,dataFactoryName,subscriptionID):
        datafactory_client =  DataFactoryManagementClient(credential,subscriptionID)
        pipelines = datafactory_client.pipelines.list_by_factory(resource_group_name=resourceGroupName,factory_name=dataFactoryName)
        PipelineList = []
        for pipeline in pipelines:
            PipelineList.append(pipeline.name)
        # RunHistory.get_master_pipeline_adf(writer,credential,subscriptionID,resourceGroupName,dataFactoryName,pipelineName)
        return PipelineList

    def getResourceGroup(subscriptionID):
        resource_client = ResourceManagementClient(credential, subscription_id=subscriptionID)
        resources = resource_client.resource_groups.list()
        resourceGroupList = []
        for resource in resources:
            # print("Resource Groupe Name : {}\t Type: {}".format(resource.name,resource.type))
            resourceGroupList.append(resource.name)
        return resourceGroupList 
    def getListOfADFs(subscriptionID, resourceGroupName):
        # resources = resource_client.resource_groups.list()
        resource_client = ResourceManagementClient(credential, subscription_id=subscriptionID)
        services = resource_client.resources.list_by_resource_group(resourceGroupName)
        ADFList = []
        for service in services:
            if (service.type == "Microsoft.DataFactory/factories"):
                # print("Data Factory Name : "+service.name+"\n")
                ADFList.append(service.name) 
        return ADFList
                
def getListOfSubscription():
    # credential = InteractiveBrowserCredential()
    subscription_client = SubscriptionClient(credential)
    subscription_list = subscription_client.subscriptions.list()
    SubscriptionList={}
    for subscription in subscription_list:
        # print("Subscription ID : {}\nSubscriptionName : {}\n".format(subscription.subscription_id, subscription.display_name))
        SubscriptionList[subscription.display_name]=subscription.subscription_id
    return SubscriptionList

 
def main():
    getListOfSubscription()
if __name__ == "__main__":
    main()
