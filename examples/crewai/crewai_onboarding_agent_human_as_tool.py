from channels import dm_with_head_of_marketing
from crewai import Agent, Crew, Task
from crewai_tools import tool
from dotenv import load_dotenv

load_dotenv()

from functionlayer import ApprovalMethod, FunctionLayer

fl = FunctionLayer(approval_method=ApprovalMethod.CLOUD)

task_prompt = """

Your task is to check the list of recently signed up customers, get info about their onboarding progress,
and send each one an email to encourage them to complete the onboarding process. You should
offer a meeting to help them where it makes sense.

If they are fully onboard, you should simply request feedback and offer a meeting.

Get approval from the head of marketing before sending

"""


@tool
def get_recently_signed_up_customers() -> list[str]:
    """get a list of customers that signed up recently"""
    return ["danny@metacorp.com", "terri@acmestuff.com"]


@tool
def get_info_about_customer(customer_email: str) -> str:
    """get info about a customer"""
    if customer_email == "danny@metacorp.com":
        return """
        This customer has completed most of the onboarding steps,
        but still needs to invite a few team members before they can be
        considered fully onboarded
        """
    else:
        return "This customer has completed all the of the onboarding steps and is actively using the product."


# no approval, human routed in at the prompt layer
@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a user"""

    # write to a local file so we can inspect after
    with open("emails.md", "a") as f:
        f.write(
            f"""{subject}
=============
To: {to}
* * *

{body}

* * *
        """
        )

    return f"Email sent to {to} with subject: {subject}"


general_agent = Agent(
    role="Onboarding Agent",
    goal="""Ensure all customers of the product are onboarded successfully""",
    backstory="""
You are the email onboarding assistant. You check on the progress customers
are making and get other information, then based on that info, you
send friendly and encouraging emails to customers to help them fully onboard
into the product.
""",
    allow_delegation=False,
    tools=[
        get_info_about_customer,
        get_recently_signed_up_customers,
        send_email,
        tool(fl.human_as_tool(dm_with_head_of_marketing)),
    ],
    verbose=True,
    crew_sharing=False,
)

task = Task(
    description=task_prompt,
    agent=general_agent,
    expected_output="A numerical answer.",
)

crew = Crew(agents=[general_agent], tasks=[task], verbose=2)


def main():
    return crew.kickoff()


if __name__ == "__main__":
    result = main()
    print("\n\n---------- RESULT ----------\n\n")
    print(result)