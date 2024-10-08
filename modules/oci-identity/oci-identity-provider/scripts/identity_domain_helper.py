import argparse
import oci
import ast

# https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm#Running_Scripts_on_a_Computer_without_a_Browser
def get_signer(config: dict):
    token_file = config['security_token_file']
    token = None
    with open(token_file, 'r') as f:
        token = f.read()
    private_key = oci.signer.load_private_key_from_file(config['key_file'])
    return oci.auth.signers.SecurityTokenSigner(token, private_key)

# https://docs.oracle.com/en-us/iaas/tools/python-sdk-examples/2.128.0/identitydomains/get_rule.py.html
def update_saml_idp_to_default_ipd_policy(operation, config_file_profile, domain_url, default_rule_id, saml_idp_id):
    config = oci.config.from_file(profile_name=config_file_profile)
    if "security_token_file" in config:
        signer = get_signer(config)
        identity_domains_client = oci.identity_domains.IdentityDomainsClient(config, domain_url, signer=signer)
    else:
        identity_domains_client = oci.identity_domains.IdentityDomainsClient(config, domain_url)
    
    get_rule_response = identity_domains_client.get_rule(rule_id=default_rule_id, attribute_sets=["all"])
    default_rule_details = get_rule_response.data
    return_node = default_rule_details._return

    for ele in return_node:
        if ele.name == "SamlIDPs":
            SamlIDPs = ast.literal_eval(ele.value) if ele.value else []

            # Append new SAML IdP ID to list of SamlIDPs
            if operation == "ADD" and saml_idp_id not in SamlIDPs:
                SamlIDPs.append(saml_idp_id)

            # Remove SAML IdP ID from list of SamlIDPs
            elif operation == "REMOVE" and saml_idp_id in SamlIDPs:
                SamlIDPs.remove(saml_idp_id)
            ele.value = str(SamlIDPs).replace("'",'"')
            print("updated SAML-IPDs=", ele)

    # PATCH update rules
    try:
        patch_rule_response = identity_domains_client.patch_rule(
            rule_id=default_rule_id,
            patch_op=oci.identity_domains.models.PatchOp(
                schemas=["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                operations=[oci.identity_domains.models.Operations(op="REPLACE", path="return", value=return_node)]
            ))
        print("Rule update successful!", patch_rule_response.data)
    except Exception as e:
        print("Rule update encountered issue, but would have updated!", e.args[0])



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-o', '--operation',  default='ADD',
                        help='ADD / REMOVE',
                        required=False)
    parser.add_argument('-p', '--config_file_profile',  default='DEFAULT', 
                        help='OCI auth profile name', 
                        required=False)  
    parser.add_argument('-u', '--domain_url',
                        help='domain url eg https://idcs-<token>.identity.oraclecloud.com:443',
                        required=True)
    parser.add_argument('-r', '--default_rule_id', default='DefaultIDPRule',
                        help='Default Identity Provider Policy if not provided ', 
                        required=False)   
    parser.add_argument('-i', '--saml_idp_id',
                        help='Default Identity Provider Policy if not provided ', 
                        required=True)
    args = parser.parse_args()
    
    update_saml_idp_to_default_ipd_policy(args.operation, args.config_file_profile, args.domain_url, args.default_rule_id, args.saml_idp_id)
    