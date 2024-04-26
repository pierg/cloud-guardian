from cloud_guardian.iam_dynamic.actions.supported import AttachUserPolicy
from cloud_guardian.iam_dynamic.model import IAMGraphMDP, Parameters
from cloud_guardian.iam_static.graph.initializers import create_graph
from cloud_guardian.iam_static.graph.plotting import save_graph_pdf
from cloud_guardian.utils.shared import data_path, output_path


def main(data_folder_name: str):
    iam_graph = create_graph(data_path / data_folder_name)

    print(iam_graph.summary())

    save_graph_pdf(iam_graph, output_path / f"{data_folder_name}.pdf")

    iam_mdp = IAMGraphMDP(iam_graph)

    users = {
        user.name: user for user in iam_mdp.graph.get_identities(filter_types=["user"])
    }
    print(f"Users: {list(users.keys())}")

    for user_name, user_data in users.items():
        available_actions = iam_mdp.get_actions(user_data.id)
        print(f"Available actions for {user_name}: {available_actions}")

    # Example with "iam:CreateUser" action
    entity = users["Eve"]  # entity performing the action
    action = "iam:CreateUser"  # action to be performed
    # parameters for the action
    parameters = Parameters({"user_name": "new_user"})
    iam_mdp.step(entity, action, parameters)
    print(iam_graph.summary())
    save_graph_pdf(iam_graph, output_path / f"{data_folder_name}_example_1.pdf")

    # We can export the trace so far:
    trace = iam_mdp.to_dict()
    print(f"Trace: {trace}")

    # We can also load a trace into a new model

    # Alternative Example with "iam:CreateUser" action by loading a trace
    # Create a new graph
    iam_graph_new = create_graph(data_path / data_folder_name)
    print(iam_graph_new.summary())
    save_graph_pdf(iam_graph_new, output_path / f"{data_folder_name}_new1.pdf")
    iam_mdp_new = IAMGraphMDP(iam_graph_new)
    iam_mdp_new.execute_trace(trace)
    print(iam_graph.summary())
    save_graph_pdf(iam_graph, output_path / f"{data_folder_name}_new1_example_1.pdf")

    # We can execute actions from dict

    # Alternative Example with "iam:CreateUser" action by loading a trace
    # Create a new graph
    iam_graph_new = create_graph(data_path / data_folder_name)
    save_graph_pdf(iam_graph_new, output_path / f"{data_folder_name}_new2.pdf")
    iam_mdp_new = IAMGraphMDP(iam_graph_new)
    step_dict = {
        "entity": "arn:aws:iam::123456789012:user/Eve",
        "action": "iam:CreateUser",
        "parameters": {"user_name": "new_user"},
    }

    iam_mdp_new.step_from_dict(step_dict)
    print(iam_graph.summary())
    save_graph_pdf(iam_graph, output_path / f"{data_folder_name}_new2_example_1.pdf")

    # TEST
    # TODO: remove
    test = AttachUserPolicy()
    test.apply(
        iam_graph,
        "arn:aws:iam::user/Alice",
        {
            "PolicyName": "ExamplePolicyAlice",
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "s3:ListAllMyBuckets",
                        "Resource": "arn:aws:s3:::*",
                    }
                ],
            },
            "Description": "Policy for ExamplePolicy",
        },
    )
    # TEST

    # Example: perform a priviledge escalation attack
    # TODO
    # Step 1 - Eve assumerole of SuperUser
    # Step 2 - Eve creates a new user
    # Step 3 - Eve creates a new policy
    # Step 4 - Eve attaches the admin policy to the new user


if __name__ == "__main__":
    main("toy_example/original")
