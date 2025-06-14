from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from whats_this_id.agents.tracklist_finder.tools.find_tracklist import FindTracklist
from whats_this_id.core.models.tracklist import Tracklist


@CrewBase
class TracklistSearchCrew:
    """WhatsThisId crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def tracklist_finder(self) -> Agent:
        return Agent(
            config=self.agents_config["tracklist_finder"],  # type: ignore[index]
            verbose=True,
            tools=[FindTracklist()],
        )

    @task
    def tracklist_search_task(self) -> Task:
        return Task(
            config=self.tasks_config["tracklist_search_task"],  # type: ignore[index]
            output_pydantic=Tracklist,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the WhatsThisId crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
