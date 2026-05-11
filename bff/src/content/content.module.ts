import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { ContentController } from './content.controller';
import { ContentService } from './content.service';

@Module({
  imports: [HttpModule],
  controllers: [ContentController],
  providers: [ContentService],
})
export class ContentModule {}
