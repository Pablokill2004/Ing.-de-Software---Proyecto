from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    bio = serializers.CharField(allow_blank=True, required=False)
    image = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('username', 'bio', 'image', 'following',)
        read_only_fields = ('username',)

    def get_image(self, obj):
        if obj.image:
            return obj.image

        return 'https://static.productionready.io/images/smiley-cyrus.jpg'

    def get_following(self, instance):
        following_ids = self.context.get('following_profile_ids', None)
        if following_ids is not None:
            return instance.pk in following_ids

        # Fallback for single-object endpoints (profile retrieve, follow/unfollow)
        request = self.context.get('request', None)
        if request is None or not request.user.is_authenticated:
            return False
        return request.user.profile.is_following(instance)
