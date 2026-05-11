import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';

@ApiTags('health')
@Controller('health')
export class HealthController {
  @Get()
  @ApiOperation({ summary: 'BFF 헬스 체크' })
  @ApiResponse({ status: 200, description: 'BFF 서버 정상 동작 중' })
  check() {
    return { status: 'ok', service: 'shortform-bff', timestamp: new Date().toISOString() };
  }
}
