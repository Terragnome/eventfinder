from controllers.auth_controller import AuthController
from controllers.user_controller import UserController
from helpers.app_helper import render
from helpers.template_helper import Template

class FollowerController:
  @AuthController.oauth2_required
  def followers():
    current_user = UserController().current_user
    follower_users = UserController().get_followers()

    vargs = {
      'users': follower_users,
      'callback': 'followers'
    }

    for user in follower_users:
      user.is_followed = current_user.is_follows_user(user)
      user.is_blocked = current_user.is_blocks_user(user)

    return render(template=Template.FOLLOWERS, vargs=vargs)

  @AuthController.oauth2_required
  def following():
    current_user = UserController().current_user
    recommended_users = UserController().get_following_recommended()
    following_users = UserController().get_following()

    vargs = {
      'recommended_users': recommended_users,
      'users': following_users,
      'callback': 'following'
    }

    for user in following_users:
      user.is_followed = current_user.is_follows_user(user)
      user.is_blocked = current_user.is_blocks_user(user)

    return render(template=Template.FOLLOWING, vargs=vargs)

  @AuthController.oauth2_required
  def blocking():
    current_user = UserController().current_user
    blocking = UserController().get_blocking()

    vargs = {
      'users': blocking,
      'callback': 'blocking'
    }

    for user in blocking:
      user.is_followed = current_user.is_follows_user(user)
      user.is_blocked = current_user.is_blocks_user(user)

    return render(template=Template.BLOCKING, vargs=vargs)