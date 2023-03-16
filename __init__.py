bl_info = {
    "name": "Categorize Sequence",
    "author": "tintwotin",
    "version": (1, 0),
    "blender": (3, 40, 0),
    "location": "Video Sequence Editor > Strip > Categorize Sequence",
    "description": "Flattens channels by moving strips of the same type into the same channels without overlapping them and rename channel headers accordingly",
    "warning": "",
    "doc_url": "",
    "category": "Sequencer",
}

import bpy
from operator import attrgetter
from collections import OrderedDict


class CategorizeSequenceOperator(bpy.types.Operator):
    """Categorize Sequence by automatic grouping strips of the same type into channels, which are renamed accordingly"""

    bl_idname = "sequencer.categorize_sequence"
    bl_label = "Categorize Sequence"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.area.type == "SEQUENCE_EDITOR"

    def execute(self, context):
        # Get the current active sequence editor
        seq_editor = bpy.context.scene.sequence_editor
        if not seq_editor:
            print("No active sequence editor found.")
            return
        selection = sorted(
            seq_editor.sequences, key=attrgetter("channel", "frame_final_start")
        )

        # Loop through each strip in the editor and group them by strip type
        strip_types = {}
        for strip in selection:
            if strip.type not in strip_types:
                strip_types[strip.type] = []
            strip_types[strip.type].append(strip)
        # Loop through each strip type and move strips into the first empty channel for that type
        for strip_type, strips in strip_types.items():
            new_channel = max(strip.channel for strip in context.sequences) + 1

            for strip in strips:
                overlap_channel = new_channel
                while overlap_channel < 128:
                    # Check if the new channel is already occupied
                    if not any(
                        strip.frame_final_start <= s.frame_final_end
                        and s.frame_final_start <= strip.frame_final_end
                        for s in strips
                    ):
                        # Move the strip to the new channel
                        strip.channel = overlap_channel
                        return
                    # Increment the channel index and check again
                    overlap_channel += 1
                # Move the strip to the new channel
                strip.channel = new_channel

        # Move everything down
        # Get the VSE sequence editor
        vse = context.scene.sequence_editor

        # Get all the strips in the VSE
        strips = vse.sequences_all

        channels_with_strips = [s.channel for s in bpy.context.scene.sequence_editor.sequences]
        lowest_channel = min(channels_with_strips)


        # Calculate the distance from the lowest strip to channel 1
        distance = lowest_channel - 1

        # Move each strip down by the distance, starting from the lowest channel
        for i in range(lowest_channel, len(vse.channels) + 1):
            for strip in strips:
                if strip.channel == i:
                    strip.channel -= distance

        # Rename Channels - Get a list of all the channels in the sequence editor
        channels = bpy.context.scene.sequence_editor.sequences_all

        # Loop through the channels from the lowest channel number to the highest
        for i, channel in enumerate(sorted(set(s.channel for s in channels))):
            # Find the strips on the current channel
            channel_strips = [s for s in channels if s.channel == channel]

            # Check if the channel is empty
            if not channel_strips:
                continue

            # Get the type of the first strip in the channel
            strip_type = channel_strips[0].type

            # Rename the channel to the strip type
            channel = context.scene.sequence_editor.channels[channel_strips[0].channel]
            channel.name = strip_type.title()
        return {"FINISHED"}


def add_categorize_sequence_operator_to_menu(self, context):
    self.layout.separator()
    self.layout.operator(CategorizeSequenceOperator.bl_idname)


def register():
    bpy.utils.register_class(CategorizeSequenceOperator)
    bpy.types.SEQUENCER_MT_strip.append(add_categorize_sequence_operator_to_menu)


def unregister():
    bpy.utils.unregister_class(CategorizeSequenceOperator)
    bpy.types.SEQUENCER_MT_strip.remove(add_categorize_sequence_operator_to_menu)


if __name__ == "__main__":
    register()
