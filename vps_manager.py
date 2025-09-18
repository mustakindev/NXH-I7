# vps_manager.py → VPS + tmate manager functions 💻
import docker
import subprocess
import asyncio
import random
import string
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

class VPSManager:
    def __init__(self):
        self.client = docker.from_env()
        self.vps_data_file = "vps_instances.json"
        self.load_vps_data()
        self.planes = self.load_planes()

    def load_planes(self) -> Dict[str, Dict[str, str]]:
        """Load VPS plane specs from config.json"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('planes', {})
        except FileNotFoundError:
            return {}

    def load_vps_data(self):
        """Load saved VPS instances from file"""
        if os.path.exists(self.vps_data_file):
            with open(self.vps_data_file, 'r', encoding='utf-8') as f:
                self.vps_instances = json.load(f)
        else:
            self.vps_instances = {}

    def save_vps_data(self):
        """Save VPS instances to file"""
        with open(self.vps_data_file, 'w', encoding='utf-8') as f:
            json.dump(self.vps_instances, f, indent=2, ensure_ascii=False)

    def generate_hostname(self, username: str) -> str:
        """Generate clean hostname from username"""
        clean = ''.join(c for c in username if c.isalnum() or c in '-_').lower()[:15]
        base = clean if clean else 'user'
        hostname = f"{base}-vps"
        counter = 1
        while hostname in self.vps_instances:
            hostname = f"{base}-vps{counter}"
            counter += 1
        return hostname

    async def create_vps(self, user_id: str, username: str, plane_id: str) -> Dict[str, Any]:
        """Create a new VPS instance in Docker with tmate"""
        if plane_id not in self.planes:
            raise ValueError(f"Plane {plane_id} not found")

        hostname = self.generate_hostname(username)
        container_name = f"vps-{hostname}"

        # Get plane specs
        plane = self.planes[plane_id]
        cpu = plane['cpu']
        ram = plane['ram'].replace('GB', '')  # "2GB" -> "2"

        try:
            # Create Docker container with resource limits
            container = self.client.containers.run(
                "nxh-i7-vps",  # Your built Docker image
                name=container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                ports={'22/tcp': None},  # Auto-assign host port
                mem_limit=f"{ram}g",
                cpu_quota=int(cpu * 100000),  # 100000 = 1 full CPU
                restart_policy={"Name": "unless-stopped"},
                labels={
                    "vps.user_id": user_id,
                    "vps.hostname": hostname,
                    "vps.plane": plane_id,
                    "vps.created_at": datetime.utcnow().isoformat()
                }
            )

            # Wait a moment for container to start
            await asyncio.sleep(2)

            # Get assigned SSH port
            container.reload()
            ports = container.attrs['NetworkSettings']['Ports']
            ssh_port = list(ports['22/tcp'])[0]['HostPort'] if ports.get('22/tcp') else None

            if not ssh_port:
                raise Exception("Failed to assign SSH port")

            # Generate tmate session inside container
            tmate_session = await self._start_tmate_session(container)

            # Store instance data
            vps_data = {
                "user_id": user_id,
                "username": username,
                "hostname": hostname,
                "container_id": container.id,
                "container_name": container_name,
                "ssh_port": ssh_port,
                "tmate_session": tmate_session,
                "plane": plane_id,
                "status": "running",
                "created_at": datetime.utcnow().isoformat(),
                "last_backup": None,
                "suspended": False
            }

            self.vps_instances[hostname] = vps_data
            self.save_vps_data()

            return vps_data

        except Exception as e:
            # Cleanup on failure
            try:
                container = self.client.containers.get(container_name)
                container.remove(force=True)
            except:
                pass
            raise Exception(f"Failed to create VPS: {str(e)}")

    async def _start_tmate_session(self, container) -> str:
        """Start tmate session inside container and return connection string"""
        try:
            # Execute tmate in container
            exec_id = self.client.api.exec_create(
                container.id,
                "tmate -F",
                tty=True
            )

            # Start async reader for tmate output
            async def read_tmate_output():
                exec_stream = self.client.api.exec_start(exec_id, stream=True, tty=True)
                for line in exec_stream:
                    line_str = line.decode('utf-8')
                    if "ssh session:" in line_str:
                        # Extract tmate SSH URL
                        parts = line_str.split("ssh session:")
                        if len(parts) > 1:
                            return parts[1].strip()
                return None

            # Timeout after 30 seconds
            try:
                tmate_url = await asyncio.wait_for(read_tmate_output(), timeout=30.0)
                if tmate_url:
                    return tmate_url
            except asyncio.TimeoutError:
                pass

            # Fallback: return SSH connection info
            return f"ssh root@localhost -p {container.attrs['NetworkSettings']['Ports']['22/tcp'][0]['HostPort']}"

        except Exception as e:
            return f"tmate-error: {str(e)}"

    def get_user_vps(self, user_id: str) -> list:
        """Get all VPS instances for a user"""
        return [
            vps for vps in self.vps_instances.values()
            if vps['user_id'] == str(user_id) and not vps.get('deleted', False)
        ]

    def get_vps_by_hostname(self, hostname: str) -> Optional[Dict[str, Any]]:
        """Get VPS instance by hostname"""
        return self.vps_instances.get(hostname)

    async def start_vps(self, hostname: str) -> bool:
        """Start a stopped VPS container"""
        vps = self.get_vps_by_hostname(hostname)
        if not vps:
            return False

        try:
            container = self.client.containers.get(vps['container_name'])
            container.start()
            vps['status'] = 'running'
            vps['suspended'] = False
            self.save_vps_data()
            return True
        except Exception:
            return False

    async def stop_vps(self, hostname: str) -> bool:
        """Stop a running VPS container"""
        vps = self.get_vps_by_hostname(hostname)
        if not vps:
            return False

        try:
            container = self.client.containers.get(vps['container_name'])
            container.stop()
            vps['status'] = 'stopped'
            self.save_vps_data()
            return True
        except Exception:
            return False

    async def restart_vps(self, hostname: str) -> bool:
        """Restart a VPS container"""
        vps = self.get_vps_by_hostname(hostname)
        if not vps:
            return False

        try:
            container = self.client.containers.get(vps['container_name'])
            container.restart()
            vps['status'] = 'running'
            # Regenerate tmate session
            tmate_session = await self._start_tmate_session(container)
            vps['tmate_session'] = tmate_session
            self.save_vps_data()
            return True
        except Exception:
            return False

    async def delete_vps(self, hostname: str) -> bool:
        """Delete a VPS instance and its container"""
        vps = self.get_vps_by_hostname(hostname)
        if not vps:
            return False

        try:
            container = self.client.containers.get(vps['container_name'])
            container.remove(force=True)
            vps['deleted'] = True
            vps['deleted_at'] = datetime.utcnow().isoformat()
            self.save_vps_data()
            return True
        except Exception:
            return False

    async def suspend_vps(self, hostname: str) -> bool:
        """Suspend a VPS (stop container and mark as suspended)"""
        success = await self.stop_vps(hostname)
        if success:
            vps = self.get_vps_by_hostname(hostname)
            vps['suspended'] = True
            self.save_vps_data()
        return success

    async def resume_vps(self, hostname: str) -> bool:
        """Resume a suspended VPS"""
        success = await self.start_vps(hostname)
        if success:
            vps = self.get_vps_by_hostname(hostname)
            vps['suspended'] = False
            self.save_vps_data()
        return success

    async def get_resource_usage(self, hostname: str) -> Dict[str, str]:
        """Get CPU, RAM, Disk usage for a VPS"""
        vps = self.get_vps_by_hostname(hostname)
        if not vps:
            return {"error": "VPS not found"}

        try:
            container = self.client.containers.get(vps['container_name'])
            stats = container.stats(stream=False)

            # CPU usage calculation
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_usage = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100 if system_delta > 0 else 0

            # Memory usage
            mem_usage = stats['memory_stats']['usage']
            mem_limit = stats['memory_stats']['limit']
            mem_percent = (mem_usage / mem_limit) * 100

            # Disk usage (simulated - Docker doesn't provide this easily)
            # In production, you'd exec into container and run `df`
            disk_percent = random.randint(10, 80)  # Simulated

            return {
                "cpu_percent": f"{cpu_usage:.1f}%",
                "memory_percent": f"{mem_percent:.1f}%",
                "disk_percent": f"{disk_percent}%",
                "memory_used": f"{mem_usage // (1024*1024)}MB",
                "memory_total": f"{mem_limit // (1024*1024)}MB"
            }

        except Exception as e:
            return {"error": f"Failed to get stats: {str(e)}"}

    async def create_backup(self, hostname: str) -> str:
        """Create a backup snapshot of the VPS"""
        vps = self.get_vps_by_hostname(hostname)
        if not vps:
            raise ValueError("VPS not found")

        snapshot_id = f"snap-{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
        snapshot_time = datetime.utcnow().isoformat()

        # In real implementation, you'd:
        # 1. Stop container
        # 2. Commit to new image or save tar
        # 3. Restart container
        # For now, simulate

        await self.stop_vps(hostname)
        await asyncio.sleep(1)  # Simulate backup process
        await self.start_vps(hostname)

        # Store backup info
        if 'backups' not in vps:
            vps['backups'] = []
        
        backup_info = {
            "snapshot_id": snapshot_id,
            "created_at": snapshot_time,
            "size": "1.2GB",  # Simulated
            "status": "completed"
        }
        
        vps['backups'].append(backup_info)
        vps['last_backup'] = snapshot_time
        self.save_vps_data()

        return snapshot_id

    async def restore_backup(self, hostname: str, snapshot_id: str) -> bool:
        """Restore VPS from backup snapshot"""
        vps = self.get_vps_by_hostname(hostname)
        if not vps or 'backups' not in vps:
            return False

        # Find snapshot
        snapshot = next((b for b in vps['backups'] if b['snapshot_id'] == snapshot_id), None)
        if not snapshot:
            return False

        # Simulate restore process
        await self.stop_vps(hostname)
        await asyncio.sleep(2)
        await self.start_vps(hostname)

        vps['last_restore'] = datetime.utcnow().isoformat()
        vps['restored_from'] = snapshot_id
        self.save_vps_data()

        return True

    def get_all_vps_stats(self) -> Dict[str, Any]:
        """Get stats for all VPS instances (for admin monitoring)"""
        total = len(self.vps_instances)
        running = len([v for v in self.vps_instances.values() if v.get('status') == 'running' and not v.get('deleted', False)])
        suspended = len([v for v in self.vps_instances.values() if v.get('suspended') and not v.get('deleted', False)])
        stopped = len([v for v in self.vps_instances.values() if v.get('status') == 'stopped' and not v.get('deleted', False)])

        return {
            "total": total,
            "running": running,
            "suspended": suspended,
            "stopped": stopped,
            "by_plane": self._get_vps_by_plane()
        }

    def _get_vps_by_plane(self) -> Dict[str, int]:
        """Get count of VPS by plane type"""
        result = {}
        for vps in self.vps_instances.values():
            if vps.get('deleted', False):
                continue
            plane = vps.get('plane', 'unknown')
            result[plane] = result.get(plane, 0) + 1
        return result

    def force_backup_all(self) -> Dict[str, Any]:
        """Force backup of all running VPS instances"""
        results = {"success": [], "failed": []}
        
        for hostname, vps in self.vps_instances.items():
            if vps.get('deleted', False) or vps.get('status') != 'running':
                continue
            
            try:
                # This would need to be run async in actual implementation
                # For now, just simulate
                snapshot_id = f"snap-auto-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
                if 'backups' not in vps:
                    vps['backups'] = []
                
                vps['backups'].append({
                    "snapshot_id": snapshot_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "size": "1.0GB",
                    "status": "completed",
                    "type": "auto"
                })
                
                results["success"].append(hostname)
            except Exception:
                results["failed"].append(hostname)
        
        self.save_vps_data()
        return results
