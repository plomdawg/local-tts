"""
Voice management tab UI component.
"""

import gradio as gr
import shutil

from core.model_manager import VoiceModel
from ui.utils import create_model_grid


def create_voice_management_tab():
    """
    Create the voice management tab for viewing and editing voice models.

    Returns:
        gradio.TabItem: The voice management tab component
    """
    with gr.Blocks() as management_tab:
        gr.Markdown("## Voice Model Management")
        gr.Markdown("View and edit your voice models.")

        # Create the model grid
        model_cards_container, _ = create_model_grid()

        with gr.Row():
            refresh_models_btn = gr.Button("Refresh Models 🔄", size="sm", min_width=50)

        # Model editing section
        gr.Markdown("## Edit Voice Model")

        with gr.Row():
            with gr.Column(scale=1):
                # Model selection
                selected_model = gr.Dropdown(
                    label="Select Model to Edit",
                    choices=[],
                    interactive=True,
                )

                # Model image
                model_image = gr.Image(
                    label="Model Image",
                    type="filepath",
                    height=200,
                    width=200,
                )

                # Image upload
                new_image = gr.Image(
                    label="Upload New Image",
                    type="filepath",
                    height=200,
                    width=200,
                )

                update_image_btn = gr.Button("Update Image", variant="primary")

            with gr.Column(scale=1):
                # Model name
                model_name = gr.Textbox(
                    label="Model Name",
                    interactive=True,
                )

                # Model transcript
                model_transcript = gr.Textbox(
                    label="Model Transcript",
                    lines=5,
                    interactive=True,
                )

                update_model_btn = gr.Button("Update Model", variant="primary")
                status_output = gr.Textbox(label="Status", interactive=False)

        def update_model_list():
            models = [model.name for model in VoiceModel.list_models()]
            return gr.update(choices=models)

        def load_model(model_name):
            if not model_name:
                return None, "", "", None

            model = VoiceModel.from_name(model_name)
            if not model:
                return None, "", "", None

            return (
                model.image_path if model.has_image else None,
                model.name,
                model.transcript if model.has_transcript else "",
                model.image_path if model.has_image else None,
            )

        def update_model_image(model_name, new_image_path):
            if not model_name or not new_image_path:
                return "Please select a model and provide a new image."

            try:
                model = VoiceModel.from_name(model_name)
                if not model:
                    return "Model not found."

                # Copy the new image
                shutil.copy2(new_image_path, model.image_path)
                return f"Image updated for model '{model_name}'"

            except Exception as e:
                return f"Error updating image: {str(e)}"

        def update_model_details(model_name, new_name, new_transcript):
            if not model_name:
                return "Please select a model to edit."

            try:
                model = VoiceModel.from_name(model_name)
                if not model:
                    return "Model not found."

                # Update name if changed
                if new_name and new_name != model_name:
                    model.rename(new_name)

                # Update transcript if changed
                if new_transcript:
                    with open(model.text_path, "w", encoding="utf-8") as f:
                        f.write(new_transcript)

                return f"Model '{model_name}' updated successfully"

            except Exception as e:
                return f"Error updating model: {str(e)}"

        # Connect the buttons
        refresh_models_btn.click(
            fn=update_model_list,
            inputs=[],
            outputs=[selected_model],
        )

        selected_model.change(
            fn=load_model,
            inputs=[selected_model],
            outputs=[model_image, model_name, model_transcript, new_image],
        )

        update_image_btn.click(
            fn=update_model_image,
            inputs=[selected_model, new_image],
            outputs=[status_output],
        )

        update_model_btn.click(
            fn=update_model_details,
            inputs=[selected_model, model_name, model_transcript],
            outputs=[status_output],
        )

        # Initialize the model list
        management_tab.load(
            fn=update_model_list,
            inputs=[],
            outputs=[selected_model],
        )

    return management_tab
