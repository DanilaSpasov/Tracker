from rest_framework import serializers

from habits.models import Habit


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = "__all__"
        read_only_fields = ("owner",)

    def validate(self, data):
        is_pleasant = data.get(
            "is_pleasant",
            getattr(self.instance, "is_pleasant", False),
        )
        reward = data.get(
            "reward",
            getattr(self.instance, "reward", ""),
        )
        related_habit = data.get(
            "related_habit",
            getattr(self.instance, "related_habit", None),
        )
        if reward and related_habit:
            raise serializers.ValidationError(
                "Нельзя одновременно указывать вознаграждение "
                "и связанную привычку."
            )
        if related_habit and not related_habit.is_pleasant:
            raise serializers.ValidationError(
                "Связанной может быть только приятная привычка."
            )
        request = self.context.get("request")
        if (
            related_habit
            and request
            and related_habit.owner_id != request.user.id
        ):
            raise serializers.ValidationError(
                {
                    "related_habit": (
                        "Можно связывать только собственные привычки."
                    )
                }
            )
        if is_pleasant and (reward or related_habit):
            raise serializers.ValidationError(
                "У приятной привычки не может быть вознаграждения "
                "или связанной привычки."
            )

        return data

    def validate_duration(self, value):
        if value > 120:
            raise serializers.ValidationError(
                "Время выполнения не может превышать 120 секунд."
            )
        return value

    def validate_frequency(self, value):
        if value < 1 or value > 7:
            raise serializers.ValidationError(
                "Периодичность выполнения должна быть от 1 до 7 дней."
            )
        return value
