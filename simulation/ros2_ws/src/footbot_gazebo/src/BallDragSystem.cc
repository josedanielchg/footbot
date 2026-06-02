#include <algorithm>
#include <cmath>
#include <memory>
#include <string>

#include <gz/math/Vector3.hh>
#include <gz/plugin/Register.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/EventManager.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/System.hh>
#include <gz/sim/components/Link.hh>
#include <gz/sim/components/Name.hh>
#include <sdf/Element.hh>

namespace footbot_gazebo
{
class BallDragSystem
    : public gz::sim::System,
      public gz::sim::ISystemConfigure,
      public gz::sim::ISystemPreUpdate
{
public:
  void Configure(
      const gz::sim::Entity &,
      const std::shared_ptr<const sdf::Element> &_sdf,
      gz::sim::EntityComponentManager &,
      gz::sim::EventManager &) override
  {
    if (_sdf->HasElement("link_name"))
      this->linkName = _sdf->Get<std::string>("link_name");
    if (_sdf->HasElement("linear_damping"))
      this->linearDamping = _sdf->Get<double>("linear_damping");
    if (_sdf->HasElement("angular_damping"))
      this->angularDamping = _sdf->Get<double>("angular_damping");
    if (_sdf->HasElement("max_force"))
      this->maxForce = _sdf->Get<double>("max_force");
    if (_sdf->HasElement("max_torque"))
      this->maxTorque = _sdf->Get<double>("max_torque");
    if (_sdf->HasElement("stop_linear_speed"))
      this->stopLinearSpeed = _sdf->Get<double>("stop_linear_speed");
    if (_sdf->HasElement("stop_angular_speed"))
      this->stopAngularSpeed = _sdf->Get<double>("stop_angular_speed");
  }

  void PreUpdate(
      const gz::sim::UpdateInfo &_info,
      gz::sim::EntityComponentManager &_ecm) override
  {
    if (_info.paused)
      return;

    _ecm.Each<gz::sim::components::Link, gz::sim::components::Name>(
      [this, &_ecm](
        const gz::sim::Entity &_entity,
        const gz::sim::components::Link *,
        const gz::sim::components::Name *_name) -> bool
      {
        if (_name == nullptr || _name->Data() != this->linkName)
          return true;

        gz::sim::Link link(_entity);
        link.EnableVelocityChecks(_ecm);

        auto linearVelocity = link.WorldLinearVelocity(_ecm);
        auto angularVelocity = link.WorldAngularVelocity(_ecm);
        if (!linearVelocity || !angularVelocity)
          return true;

        gz::math::Vector3d horizontalVelocity(
            linearVelocity->X(),
            linearVelocity->Y(),
            0.0);
        gz::math::Vector3d angular = *angularVelocity;

        if (horizontalVelocity.Length() <= this->stopLinearSpeed &&
            angular.Length() <= this->stopAngularSpeed)
        {
          link.SetLinearVelocity(_ecm, gz::math::Vector3d::Zero);
          link.SetAngularVelocity(_ecm, gz::math::Vector3d::Zero);
          return true;
        }

        gz::math::Vector3d force =
          this->ClampVector(-this->linearDamping * horizontalVelocity,
                            this->maxForce);
        gz::math::Vector3d torque =
          this->ClampVector(-this->angularDamping * angular,
                            this->maxTorque);

        link.AddWorldWrench(_ecm, force, torque);
        return true;
      });
  }

private:
  gz::math::Vector3d ClampVector(
      const gz::math::Vector3d &_value,
      double _maxLength) const
  {
    if (_maxLength <= 0.0)
      return gz::math::Vector3d::Zero;

    double length = _value.Length();
    if (length <= _maxLength || length <= 0.0)
      return _value;

    return _value.Normalized() * _maxLength;
  }

  std::string linkName{"ball_link"};
  double linearDamping{0.18};
  double angularDamping{0.0012};
  double maxForce{0.30};
  double maxTorque{0.015};
  double stopLinearSpeed{0.02};
  double stopAngularSpeed{0.35};
};
}

IGNITION_ADD_PLUGIN(
    footbot_gazebo::BallDragSystem,
    gz::sim::System,
    gz::sim::ISystemConfigure,
    gz::sim::ISystemPreUpdate)

IGNITION_ADD_PLUGIN_ALIAS(
    footbot_gazebo::BallDragSystem,
    "footbot_gazebo::BallDragSystem")
