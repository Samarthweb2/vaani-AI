"""Interactive CLI Simulator for testing @vaaniai mentions locally."""

import sys
from typing import Optional
from vaani.agent import VaaniAgent
from vaani.config import Settings, get_settings


def run_simulator(agent: Optional[VaaniAgent] = None) -> None:
    """Run an interactive console simulator for Vaani AI."""
    if agent is None:
        agent = VaaniAgent()

    bot_handle = agent.settings.bot_handle
    bot_mention = agent.settings.bot_mention

    print("=" * 65)
    print(f"        Vaani AI ({bot_mention}) - Social Media Agent Simulator")
    print("=" * 65)
    print(f"  * Hugging Face Mode: {agent.settings.hf_mode}")
    print(f"  * Model ID:          {agent.settings.hf_model_id}")
    print(f"  * LoRA Weights:      {agent.settings.hf_lora_path or 'None (Base model)'}")
    print(f"  * Dataset Log:       {agent.settings.dataset_path}")
    print(f"  * Existing Samples:  {agent.dataset_collector.count_samples()}")
    print("-" * 65)
    print(f"How to use: Type a mock tweet mentioning {bot_mention}")
    print(f"Example:    {bot_mention} what are the best tips for learning Python?")
    print("Commands:   'history' to view recent mentions, 'exit' or 'quit' to stop.")
    print("=" * 65)
    print()

    while True:
        try:
            user_input = input("You > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting simulator. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("Exiting simulator. Goodbye!")
            break

        if user_input.lower() == "history":
            history = agent.storage.get_recent_history(5)
            if not history:
                print("[Storage] No processed mentions recorded yet.\n")
            else:
                print("\n--- Recent Processed Mentions ---")
                for row in history:
                    print(f"[{row['processed_at']}] Query: {row['query_text']}")
                    print(f"Reply: {row['response_text']}\n")
            continue

        # If user didn't type @vaaniai, remind them or automatically process
        if bot_mention.lower() not in user_input.lower() and f"@{bot_handle}".lower() not in user_input.lower():
            print(f"Note: Simulating mention tag -> prepending '{bot_mention} ' to your tweet.")
            tweet_text = f"{bot_mention} {user_input}"
        else:
            tweet_text = user_input

        print(f"\n[Vaani AI processing mention: '{tweet_text}']...")

        try:
            full_response, chunks = agent.solve_mention_query(
                raw_text=tweet_text,
                author="simulator_user",
                source="cli_simulator"
            )

            print("\n" + "=" * 40)
            print(f"Vaani AI ({bot_mention}) Response:")
            print("=" * 40)
            for idx, chunk in enumerate(chunks, 1):
                if len(chunks) > 1:
                    print(f"\n[Tweet {idx}/{len(chunks)} - {len(chunk)} chars]:")
                else:
                    print(f"\n[Tweet - {len(chunk)} chars]:")
                print(chunk)
            print("=" * 40)

            # Store in local SQLite as simulated tweet
            sim_id = f"sim_{agent.dataset_collector.count_samples()}"
            agent.storage.record_mention(
                tweet_id=sim_id,
                author_id="0",
                author_username="simulator_user",
                query_text=tweet_text,
                response_text=full_response,
                reply_tweet_id=None
            )

            print(f"[Dataset] Logged to '{agent.settings.dataset_path}' (Total: {agent.dataset_collector.count_samples()} samples)")
            print()

        except Exception as e:
            print(f"\n[Error] Failed to process query: {e}\n")


if __name__ == "__main__":
    run_simulator()
